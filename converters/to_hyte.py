#!/usr/bin/env python3
"""Convert my datasets -> HyTE repo input format, ZERO code changes.

HyTE (malllabiisc/HyTE) hardcodes paths 'data/<data_type>/<version>/...' with
data_type restricted to {yago, wiki_data}. Trick: each of my datasets is
materialised under data_ready/hyte/<ds>/data/yago/large/ and the original
time_proj.py is launched with cwd = data_ready/hyte/<ds>/ and -data_type yago
-version large. No repo file is touched.

Time handling: HyTE reads the time fields as 4-char "year" strings
(create_id_labels drops rows whose token length != 4). My data are time
points, so start = end = token:
  - finreflect: real years '2014'..'2024'
  - icews18/gdelt: day index from dataset min date, encoded '1000'+k
    (4-char pseudo-year; ordinal structure preserved, mapping in time_map.json)
HyTE then applies its own original frequency binning (create_year2id,
count>300) on these tokens — its native protocol.

Files written (integer ids, tab-separated):
  train.txt  : h r t start end            (ids; start=end=token)
  valid.txt / test.txt : same 5-col format
  entity2id.txt / relation2id.txt : name \t id
  triple2id.txt : training triples as 'h r t' ids (negative-sampling filter;
                  train-only to avoid valid/test leakage)
"""
import csv, json, pathlib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]

def read(ds):
    src = ROOT / "data_source" / ds
    out = {}
    for split in ("train", "valid", "test"):
        rows = []
        with open(src / f"{split}.tsv") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if ds == "finreflect":
                    k = r["year"].strip()
                else:
                    tcol = "date" if "date" in r else "datetime"
                    k = r[tcol].strip()[:10]
                rows.append((r["subject"], r["relation"], r["object"], k))
        out[split] = rows
    return out

def convert(ds):
    data = read(ds)
    allrows = [q for p in data.values() for q in p]
    keys = sorted({q[3] for q in allrows})
    if ds == "finreflect":
        tok = {k: k for k in keys}                       # real 4-char years
    else:
        dmin = date.fromisoformat(keys[0])
        tok = {k: str(1000 + (date.fromisoformat(k) - dmin).days) for k in keys}
        assert all(len(v) == 4 for v in tok.values())
    # HyTE builds its time bins from TRAIN times only; valid/test tokens outside
    # the train range crash get_span_ids (no bin). Clamp out-of-range eval
    # tokens to the nearest train token (HyTE cannot embed unseen time bins).
    train_tok_vals = sorted({int(tok[q[3]]) for q in data["train"]})
    tmin, tmax = train_tok_vals[0], train_tok_vals[-1]
    clamped = 0
    def clamp(t):
        nonlocal clamped
        v = int(tok[t])
        if v < tmin or v > tmax:
            clamped += 1
            return str(max(tmin, min(tmax, v)))
        return tok[t]

    ents = sorted({q[0] for q in allrows} | {q[2] for q in allrows})
    rels = sorted({q[1] for q in allrows})
    eid = {e: i for i, e in enumerate(ents)}
    rid = {r: i for i, r in enumerate(rels)}

    dst = ROOT / "data_ready" / "hyte" / ds / "data" / "yago" / "large"
    dst.mkdir(parents=True, exist_ok=True)
    with open(dst / "entity2id.txt", "w") as f:
        for e, i in eid.items(): f.write(f"{e}\t{i}\n")
    with open(dst / "relation2id.txt", "w") as f:
        for r, i in rid.items(): f.write(f"{r}\t{i}\n")
    for split, rows in data.items():
        with open(dst / f"{split}.txt", "w") as f:
            for h, r, t, k in rows:
                tk = tok[k] if split == "train" else clamp(k)
                f.write(f"{eid[h]}\t{rid[r]}\t{eid[t]}\t{tk}\t{tk}\n")
    with open(dst / "triple2id.txt", "w") as f:
        for h, r, t, k in data["train"]:
            f.write(f"{eid[h]}\t{rid[r]}\t{eid[t]}\n")
    with open(dst / "time_map.json", "w") as f:
        json.dump({"real_to_token": tok,
                   "train_token_range": [tmin, tmax],
                   "eval_tokens_clamped_to_train_range": clamped}, f, indent=2)
    if clamped:
        print(f"  note: {clamped} valid/test timestamps clamped into train range [{tmin},{tmax}]")
    print(f"{ds}: ents={len(ents)} rels={len(rels)} times={len(keys)} "
          f"splits={[len(data[s]) for s in ('train','valid','test')]}")

if __name__ == "__main__":
    import sys
    for ds in (sys.argv[1:] or ["finreflect", "icews18", "gdelt"]):
        convert(ds)
