#!/usr/bin/env python3
"""Convert FinReflect -> HyTE repo input format using its REAL time INTERVAL
(start_date / end_date), ZERO code changes to HyTE.

This is the *interval variant* for HyTE only (finreflect only). HyTE is natively
an interval method: time_proj.py reads columns [3] and [4] as (start, end) and
getOneHot() spreads each triple across every year-bin in [start, end]. The
default converter (to_hyte.py) feeds start=end (time-point). Here we feed the
real reporting interval recovered from FinReflect's start_date/end_date columns.

Why a join: the shared split files (data_source/finreflect/{train,valid,test}.tsv)
carry only (subject, relation, object, year) — start/end live only in the
original finreflect_sample2000.tsv. We therefore build a lookup
  (entity, relationship, target, year) -> (start_year, end_year)
from the original file and join it onto the split rows. The split itself is
NEVER modified (the other three methods keep using it untouched).

Missing / noisy end_date handling (the 199 'default_*' placeholders, etc.):
  1. parse a 4-digit year from start_date / end_date;
  2. if a field is unparseable ('default_*') -> fall back to the clean `year`
     column (always present; this is exactly the timestamp the point-HyTE uses,
     so the row gracefully degrades to the point behaviour);
  3. if end_year < start_year (noise) -> collapse to a point (end = start);
  4. on dedup collision (same quad, several originals) -> widest interval
     (min start_year, max end_year);
  5. clamp valid/test endpoints into the train year range (HyTE bins from train
     only; finreflect is a random split so this is ~no-op, kept for safety).

Output: data_ready/hyte_interval/finreflect/data/yago/large/
  train/valid/test.txt : h_id r_id t_id start_year end_year   (real interval)
  entity2id.txt relation2id.txt triple2id.txt                 (as to_hyte.py)
  time_map.json : policy stats (real intervals, fallbacks, reversed, clamped)
"""
import csv, json, re, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
DS = "finreflect"
YEAR_RE = re.compile(r"(19|20)\d{2}")


def parse_year(s, fallback):
    """First 4-digit year in s, else the clean `year` column value."""
    m = YEAR_RE.search(s or "")
    return m.group(0) if m else fallback


def build_interval_map():
    """(entity,relationship,target,year) -> (min_start_year, max_end_year)."""
    src = ROOT / "data_source" / DS / "finreflect_sample2000.tsv"
    agg = {}
    stats = defaultdict(int)
    with open(src) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            yr = r["year"].strip()
            key = (r["entity"].strip(), r["relationship"].strip(),
                   r["target"].strip(), yr)
            s_raw, e_raw = r.get("start_date", ""), r.get("end_date", "")
            sy = parse_year(s_raw, yr)
            ey = parse_year(e_raw, yr)
            if YEAR_RE.search(s_raw or "") is None:
                stats["start_fallback_to_year"] += 1
            if YEAR_RE.search(e_raw or "") is None:
                stats["end_fallback_to_year"] += 1
            if int(ey) < int(sy):
                stats["reversed_collapsed"] += 1
                ey = sy
            if key in agg:
                ps, pe = agg[key]
                agg[key] = (min(ps, sy), max(pe, ey))
            else:
                agg[key] = (sy, ey)
    return agg, stats


def read_split():
    out = {}
    for split in ("train", "valid", "test"):
        rows = []
        with open(ROOT / "data_source" / DS / f"{split}.tsv") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                rows.append((r["subject"].strip(), r["relation"].strip(),
                             r["object"].strip(), r["year"].strip()))
        out[split] = rows
    return out


def convert():
    imap, stats = build_interval_map()
    data = read_split()
    allrows = [q for p in data.values() for q in p]

    # interval per split row (join; fallback to point if quad somehow absent)
    def interval(s, r, o, y):
        return imap.get((s, r, o, y), (y, y))

    # train year range for clamping eval endpoints
    tr_years = []
    for s, r, o, y in data["train"]:
        a, b = interval(s, r, o, y)
        tr_years += [int(a), int(b)]
    tmin, tmax = min(tr_years), max(tr_years)
    clamped = 0

    def clamp(a, b):
        nonlocal clamped
        ca, cb = max(tmin, min(tmax, int(a))), max(tmin, min(tmax, int(b)))
        if (ca, cb) != (int(a), int(b)):
            clamped += 1
        return str(ca), str(cb)

    ents = sorted({q[0] for q in allrows} | {q[2] for q in allrows})
    rels = sorted({q[1] for q in allrows})
    eid = {e: i for i, e in enumerate(ents)}
    rid = {r: i for i, r in enumerate(rels)}

    dst = ROOT / "data_ready" / "hyte_interval" / DS / "data" / "yago" / "large"
    dst.mkdir(parents=True, exist_ok=True)
    with open(dst / "entity2id.txt", "w") as f:
        for e, i in eid.items(): f.write(f"{e}\t{i}\n")
    with open(dst / "relation2id.txt", "w") as f:
        for r, i in rid.items(): f.write(f"{r}\t{i}\n")

    real_interval = 0
    for split, rows in data.items():
        with open(dst / f"{split}.txt", "w") as f:
            for s, r, o, y in rows:
                a, b = interval(s, r, o, y)
                if split != "train":
                    a, b = clamp(a, b)
                if a != b:
                    real_interval += 1
                f.write(f"{eid[s]}\t{rid[r]}\t{eid[o]}\t{a}\t{b}\n")
    with open(dst / "triple2id.txt", "w") as f:
        for s, r, o, y in data["train"]:
            f.write(f"{eid[s]}\t{rid[r]}\t{eid[o]}\n")

    meta = {"variant": "interval", "dataset": DS,
            "train_year_range": [tmin, tmax],
            "rows_with_real_interval(start!=end)": real_interval,
            "eval_endpoints_clamped_to_train_range": clamped,
            **{k: v for k, v in stats.items()}}
    with open(dst / "time_map.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"{DS} (interval): ents={len(ents)} rels={len(rels)} "
          f"splits={[len(data[s]) for s in ('train','valid','test')]} "
          f"real_intervals={real_interval} clamped={clamped}")
    print("  policy:", dict(stats))


if __name__ == "__main__":
    convert()
