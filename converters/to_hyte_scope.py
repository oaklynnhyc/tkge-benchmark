#!/usr/bin/env python3
"""Build working dirs for HyTE TIME-PREDICTION (temporal scoping) runs,
year vs month granularity, ZERO code changes to HyTE.

HyTE's original time-prediction entry point (time_proj_tdns_scope.py) reads
`data/yago/large/valid.txt` as its evaluation file (its --test_data is
hardwired to that path) and has no separate test pass. To obtain TEST scores
without touching code we prepare, per granularity, two identical working
copies of the point dataset that differ ONLY in which split sits at the
evaluated filename:

    data_ready/hyte_scope/finreflect_<gran>_sel/   valid.txt = valid split
    data_ready/hyte_scope/finreflect_<gran>_test/  valid.txt = test  split

The runner trains both with IDENTICAL args+seed (the repo seeds tf/np/random),
picks the best epoch from the _sel run via the original result_eval_time.py,
and reads the _test run's dump at that epoch. Model identity across the twin
runs is verified by comparing checkpoint bytes.

Sources (must exist; run to_hyte.py / to_hyte_month.py first):
    year : data_ready/hyte/finreflect/data/yago/large
    month: data_ready/hyte/finreflect_month/data/yago/large
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRCDIR = {"year": ROOT / "data_ready" / "hyte" / "finreflect" / "data" / "yago" / "large",
          "month": ROOT / "data_ready" / "hyte" / "finreflect_month" / "data" / "yago" / "large"}

def build(gran):
    src = SRCDIR[gran]
    assert src.exists(), f"source missing: {src} (run to_hyte.py / to_hyte_month.py first)"
    for variant in ("sel", "test"):
        dst = (ROOT / "data_ready" / "hyte_scope" /
               f"finreflect_{gran}_{variant}" / "data" / "yago" / "large")
        if dst.parent.parent.parent.exists():
            shutil.rmtree(dst.parent.parent.parent)
        dst.mkdir(parents=True)
        for f in src.iterdir():
            shutil.copy(f, dst / f.name)
        if variant == "test":
            # the file HyTE evaluates is literally 'valid.txt'
            shutil.copy(src / "test.txt", dst / "valid.txt")
        n = sum(1 for _ in open(dst / "valid.txt"))
        print(f"{gran}/{variant}: valid.txt <- {'test' if variant=='test' else 'valid'} split ({n} rows)")

if __name__ == "__main__":
    for g in (sys.argv[1:] or ["year", "month"]):
        build(g)
