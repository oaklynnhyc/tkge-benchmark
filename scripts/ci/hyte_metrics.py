#!/usr/bin/env python3
"""Compute MRR / Hits@1/3/10 from HyTE's own test prediction dumps.

HyTE's result_eval.py reports MR and Hits@10 only; it derives ranks by sorting
the dumped score vectors ascending and taking the gold entity's position
(0-based; +1 for MR). This script reproduces EXACTLY that rank definition from
the same dump files (results/<name>/test_{head,tail}_pred_<E>.txt + test.txt)
and additionally reports MRR / Hits@1/3 from those ranks. Raw (unfiltered)
protocol, as in the original HyTE evaluation. Post-processing only — no
original code is modified.
An optional 5th arg "interval" switches to the interval variant: it reads the
dumps under data_ready/hyte_interval/<ds>/ and writes results/hyte_interval_<ds>.json
(same rank definition; only the input data carries real start!=end intervals).
Usage: hyte_metrics.py <dataset> <mode> <run_name> <best_epoch> [interval]
"""
import json, pathlib, subprocess, sys
import numpy as np

ds, mode, name, best = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
variant = sys.argv[5] if len(sys.argv) > 5 else ""
sub = "hyte_interval" if variant == "interval" else "hyte"
ROOT = pathlib.Path(__file__).resolve().parents[2]
rdir = ROOT / "data_ready" / sub / ds / "results" / name

gold = [l.split() for l in (rdir / "test.txt").read_text().splitlines()]
ranks = []
for side, col in (("head", 0), ("tail", 2)):
    with open(rdir / f"test_{side}_pred_{best}.txt") as f:
        for i, line in enumerate(f):
            scores = np.fromstring(line, sep=" ")
            g = int(gold[i][col])
            order = np.argsort(scores, kind="stable")     # ascending, as original
            rank0 = int(np.where(order == g)[0][0])       # 0-based position
            ranks.append(rank0)
r = np.array(ranks, dtype=float)
metrics = {"MRR": float(np.mean(1.0 / (r + 1))), "MR": float(np.mean(r) + 1),
           "Hits@1": float(np.mean(r < 1)), "Hits@3": float(np.mean(r < 3)),
           "Hits@10": float(np.mean(r < 10))}

REPO = ROOT / "repos" / "HyTE"
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                       capture_output=True, text=True).stdout.strip()
dirty = "\n".join(l for l in dirty.splitlines()
                  if "__pycache__" not in l and not l.endswith(".pyc"))
is_intv = variant == "interval"
out = {"method": "HYTE(interval)" if is_intv else "HYTE",
       "dataset": ds, "mode": mode, **metrics,
       "best_valid_epoch": int(best), "n_test_ranks": len(ranks),
       "eval_protocol": "HyTE native dumps: RAW (unfiltered), head+tail averaged; "
                        "MRR/Hits@1/3 post-computed from the repo's own score dumps "
                        "using its exact rank definition",
       "repo": "github.com/malllabiisc/HyTE", "repo_commit": commit,
       "repo_diff": dirty or "CLEAN (zero modification)",
       "entry_point": f"python time_proj.py -name {name} ... (see runs/{name}.log)",
       "notes": ("REAL time interval (start_date/end_date) fed via HyTE's native "
                 "start/end columns; missing/default end_date falls back to the "
                 "`year` column; see converters/to_hyte_interval.py + its time_map.json"
                 if is_intv else
                 "data served under hardcoded data/yago/large alias; time points as "
                 "4-char tokens, HyTE's own >300-count binning applied")}
res = ROOT / "results"; res.mkdir(exist_ok=True)
(res / f"{'hyte_interval' if is_intv else 'hyte'}_{ds}.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
