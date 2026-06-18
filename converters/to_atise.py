#!/usr/bin/env python3
"""Convert my datasets -> ATISE repo (ATiSE/TeRo) input format, with ZERO changes
to the original code.

ATISE repo (soledad921/ATISE) hardcodes dataset names. Trick used here:
each of my datasets is materialised under an alias directory literally named
`icews05-15/` (whose hardcoded params are start_date=2005-01-01, n_time=4017),
and the original Main.py is launched with cwd = data_ready/atise/<dataset>/.

Time handling (all three datasets are time-POINT data):
- Each real timestamp is mapped to a synthetic date 2005-01-01 + k days, where
  k = ordinal time index (FinReflect: year - min_year; ICEWS18/GDELT:
  calendar-day offset from the dataset's min date). This is a pure, invertible
  data transformation: the model only ever consumes the integer day index.
- The real->synthetic mapping is recorded in time_map.json for traceability.

Output per dataset: data_ready/atise/<ds>/icews05-15/
    train.txt valid.txt test.txt   (head \t rel \t tail \t YYYY-MM-DD, no header)
    entity2id.txt relation2id.txt  (built over all splits)
    time_map.json
"""
import csv, json, pathlib
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE_DATE = date(2005, 1, 1)
N_TIME_LIMIT = 4017  # hardcoded n_time for the 'icews05-15' alias

def read_rows(ds):
    """Yield (head, rel, tail, time_index_key) for each split."""
    src = ROOT / "data_source" / ds
    out = {}
    for split in ("train", "valid", "test"):
        rows = []
        with open(src / f"{split}.tsv") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if ds == "finreflect":
                    key = r["year"].strip()            # yearly granularity
                else:
                    tcol = "date" if "date" in r else "datetime"
                    key = r[tcol].strip()[:10]          # daily granularity
                rows.append((r["subject"], r["relation"], r["object"], key))
        out[split] = rows
    return out

def convert(ds):
    data = read_rows(ds)
    allrows = [q for part in data.values() for q in part]
    # ordinal time index over the union of all splits
    keys = sorted({q[3] for q in allrows})
    if ds == "finreflect":
        kmin = int(keys[0])
        idx = {k: int(k) - kmin for k in keys}
    else:
        dmin = date.fromisoformat(keys[0])
        idx = {k: (date.fromisoformat(k) - dmin).days for k in keys}
    assert max(idx.values()) < N_TIME_LIMIT, f"{ds}: time span exceeds alias n_time"

    ents = sorted({q[0] for q in allrows} | {q[2] for q in allrows})
    rels = sorted({q[1] for q in allrows})

    dst = ROOT / "data_ready" / "atise" / ds / "icews05-15"
    dst.mkdir(parents=True, exist_ok=True)
    with open(dst / "entity2id.txt", "w") as f:
        for i, e in enumerate(ents):
            f.write(f"{e}\t{i}\n")
    with open(dst / "relation2id.txt", "w") as f:
        for i, r in enumerate(rels):
            f.write(f"{r}\t{i}\n")
    for split, rows in data.items():
        with open(dst / f"{split}.txt", "w") as f:
            for h, r, t, k in rows:
                syn = BASE_DATE + timedelta(days=idx[k])
                f.write(f"{h}\t{r}\t{t}\t{syn.isoformat()}\n")
    with open(dst / "time_map.json", "w") as f:
        json.dump({"base_synthetic_date": BASE_DATE.isoformat(),
                   "granularity": "year" if ds == "finreflect" else "day",
                   "real_to_index": idx}, f, indent=2)
    print(f"{ds}: ents={len(ents)} rels={len(rels)} times={len(keys)} "
          f"train/valid/test={[len(data[s]) for s in ('train','valid','test')]}")

if __name__ == "__main__":
    import sys
    for ds in (sys.argv[1:] or ["finreflect", "icews18", "gdelt"]):
        convert(ds)
