#!/usr/bin/env python3
"""Canonical FinReflect train/valid/test split (run once; all four methods share it).

- Input : data_source/finreflect/finreflect_sample2000.tsv (12-col, header)
- Output: data_source/finreflect/{train,valid,test}.tsv
          4-col with header: subject  relation  object  year
- Dedupe on (subject, relation, object, year) BEFORE splitting to avoid leakage.
- Deterministic: seed=42, shuffle, 80/10/10.
"""
import csv, json, random, pathlib

SRC = pathlib.Path(__file__).resolve().parents[1] / "data_source" / "finreflect"
SEED = 42

def main():
    rows, seen = [], set()
    with open(SRC / "finreflect_sample2000.tsv") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            quad = (r["entity"].strip(), r["relationship"].strip(),
                    r["target"].strip(), r["year"].strip())
            if all(quad) and quad not in seen:
                seen.add(quad)
                rows.append(quad)
    random.Random(SEED).shuffle(rows)
    n = len(rows)
    n_tr, n_va = int(n * 0.8), int(n * 0.1)
    splits = {"train": rows[:n_tr],
              "valid": rows[n_tr:n_tr + n_va],
              "test":  rows[n_tr + n_va:]}
    for name, part in splits.items():
        with open(SRC / f"{name}.tsv", "w") as f:
            f.write("subject\trelation\tobject\tyear\n")
            for q in part:
                f.write("\t".join(q) + "\n")
    meta = {"seed": SEED, "dedup_from": 2000, "unique_quads": n,
            "counts": {k: len(v) for k, v in splits.items()},
            "split": "80/10/10 deterministic shuffle"}
    with open(SRC / "split_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(meta)

if __name__ == "__main__":
    main()
