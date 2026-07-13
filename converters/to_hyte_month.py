#!/usr/bin/env python3
"""FinReflect -> HyTE input at MONTH granularity (time-point), ZERO code changes.

Contrast dataset to the existing year-granularity `finreflect` (to_hyte.py,
UNTOUCHED). Introduced purely as a new dataset directory `finreflect_month`
served through the same hardcoded data/yago/large alias.

Token design (HyTE requires exactly-4-char numeric time tokens):
    token = 1000 + (year - MIN_YEAR)*12 + (month-1)      # ordinal month index
    e.g. 2014-01 -> 1000, 2024-12 -> 1131  (4 chars for spans up to ~750 years)

Month source: the canonical split files carry only `year`, so the month is
joined back from data_source/finreflect/finreflect_sample2000.tsv via
(subject, relation, object, year) -> start_date. Rules (recorded in
time_map.json):
  - month = month parsed from start_date ('January 2020' style);
    unparseable (default_* placeholders) -> January (the dominant reporting
    convention; also makes such rows equivalent to the year variant).
  - duplicate quads with different start months -> earliest month (min token),
    deterministic.
  - split membership is NEVER changed: same train/valid/test as all methods.
  - eval tokens outside the train token range are clamped (same rule as
    to_hyte.py; random split so usually ~0).
  - entity2id / relation2id are built with the same sorted rule as to_hyte.py,
    hence IDENTICAL ids to the year variant (same split, same entities).

Output: data_ready/hyte/finreflect_month/data/yago/large/
    train/valid/test.txt (h r t tok tok), entity2id.txt, relation2id.txt,
    triple2id.txt (train-only), time_map.json
"""
import csv, json, pathlib, re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data_source" / "finreflect"
MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

def build_month_lookup():
    """(subject, relation, object, year) -> earliest parsed start month (1-12).
    Falls back to 1 (January) when no start_date in the group parses."""
    look = defaultdict(list)
    stats = {"rows": 0, "parsed_month": 0, "fallback_january": 0,
             "collision_groups": 0}
    with open(SRC / "finreflect_sample2000.tsv") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            quad = (r["entity"].strip(), r["relationship"].strip(),
                    r["target"].strip(), r["year"].strip())
            stats["rows"] += 1
            m = re.match(r"([A-Z][a-z]+) \d{4}$", r["start_date"].strip())
            mon = MONTHS.get(m.group(1)) if m else None
            if mon:
                stats["parsed_month"] += 1
                look[quad].append(mon)
    lut = {}
    for quad, mons in look.items():
        if len(set(mons)) > 1:
            stats["collision_groups"] += 1
        lut[quad] = min(mons)
    stats["quads_with_month"] = len(lut)
    return lut, stats

def main():
    lut, stats = build_month_lookup()
    years = []
    data = {}
    for split in ("train", "valid", "test"):
        rows = []
        with open(SRC / f"{split}.tsv") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                q = (r["subject"], r["relation"], r["object"], r["year"])
                rows.append(q)
                years.append(int(r["year"]))
        data[split] = rows
    ymin = min(years)

    fallback = 0
    def token(q):
        nonlocal fallback
        mon = lut.get(q)
        if mon is None:
            fallback += 1
            mon = 1
        t = 1000 + (int(q[3]) - ymin) * 12 + (mon - 1)
        s = str(t)
        assert len(s) == 4, s
        return s

    tok = {q: token(q) for split in data.values() for q in split}
    allrows = [q for p in data.values() for q in p]
    ents = sorted({q[0] for q in allrows} | {q[2] for q in allrows})
    rels = sorted({q[1] for q in allrows})
    eid = {e: i for i, e in enumerate(ents)}
    rid = {r: i for i, r in enumerate(rels)}

    train_vals = sorted({int(tok[q]) for q in data["train"]})
    tmin, tmax = train_vals[0], train_vals[-1]
    clamped = 0
    def clamp(q):
        nonlocal clamped
        v = int(tok[q])
        if v < tmin or v > tmax:
            clamped += 1
            return str(max(tmin, min(tmax, v)))
        return tok[q]

    dst = ROOT / "data_ready" / "hyte" / "finreflect_month" / "data" / "yago" / "large"
    dst.mkdir(parents=True, exist_ok=True)
    with open(dst / "entity2id.txt", "w") as f:
        for e, i in eid.items(): f.write(f"{e}\t{i}\n")
    with open(dst / "relation2id.txt", "w") as f:
        for r, i in rid.items(): f.write(f"{r}\t{i}\n")
    for split, rows in data.items():
        with open(dst / f"{split}.txt", "w") as f:
            for q in rows:
                tk = tok[q] if split == "train" else clamp(q)
                f.write(f"{eid[q[0]]}\t{rid[q[1]]}\t{eid[q[2]]}\t{tk}\t{tk}\n")
    with open(dst / "triple2id.txt", "w") as f:
        for q in data["train"]:
            f.write(f"{eid[q[0]]}\t{rid[q[1]]}\t{eid[q[2]]}\n")
    meta = {**stats, "min_year": ymin, "token_rule": "1000+(year-min_year)*12+(month-1)",
            "split_rows_fallback_january": fallback,
            "train_token_range": [tmin, tmax],
            "eval_tokens_clamped": clamped,
            "distinct_month_tokens": len(set(tok.values()))}
    with open(dst / "time_map.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
