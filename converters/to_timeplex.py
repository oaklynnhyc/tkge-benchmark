#!/usr/bin/env python3
"""Convert my datasets -> tkbi repo (TIMEPLEX) input format, ZERO code changes.

tkbi (dair-iitd/tkbi) selects time-encoding by DATASET NAME:
  kb.Datamap.check_date_validity(): name.lower().startswith('icews')
    -> day-level encoding of 'YYYY-MM-DD'; otherwise -> 4-char year string.
Therefore (pure naming/aliasing, no code touched):
  - finreflect   -> dir 'finreflect',  time = 'YYYY' (yearly, natural for it)
  - icews18      -> dir 'icews18',     time = 'YYYY-MM-DD' (real dates)
  - gdelt        -> dir 'icews-gdelt', time = 'YYYY-MM-DD' (real dates;
                    the icews- prefix only selects the day-level code path)

main.py also hardcodes a filter datamap at './data/<ds>', so the runner
creates data_ready/timeplex/data -> '.' symlink and uses cwd=data_ready/timeplex
with --data_repository_root ./data .

Output: data_ready/timeplex/<alias>/{train,valid,test}.txt
        (s \t r \t o \t time ; no header; entity map built by tkbi itself)
"""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ALIAS = {"finreflect": "finreflect", "icews18": "icews18", "gdelt": "icews-gdelt"}

def convert(ds):
    src = ROOT / "data_source" / ds
    dst = ROOT / "data_ready" / "timeplex" / ALIAS[ds]
    dst.mkdir(parents=True, exist_ok=True)
    n = {}
    for split in ("train", "valid", "test"):
        with open(src / f"{split}.tsv") as fi, open(dst / f"{split}.txt", "w") as fo:
            rows = list(csv.DictReader(fi, delimiter="\t"))
            for r in rows:
                if ds == "finreflect":
                    t = r["year"].strip()                       # 'YYYY'
                else:
                    tcol = "date" if "date" in r else "datetime"
                    t = r[tcol].strip()[:10]                    # 'YYYY-MM-DD'
                fo.write(f"{r['subject']}\t{r['relation']}\t{r['object']}\t{t}\n")
            n[split] = len(rows)
    print(f"{ds} -> {ALIAS[ds]}: {n}")

if __name__ == "__main__":
    import sys
    for ds in (sys.argv[1:] or list(ALIAS)):
        convert(ds)
