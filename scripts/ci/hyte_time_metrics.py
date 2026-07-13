#!/usr/bin/env python3
"""TIME-prediction metrics from HyTE's own temporal-scoping dumps.

Rank definition = EXACTLY result_eval_time.py's: per test triple sort the
dumped time-bin score vector ascending, gold rank = min position over the gold
span [start_lbl, end_lbl] (our data are points, start==end -> exact bin).
Reported (all post-processing; no original code modified):
  strict_top1  : rank == 0  (完全命中該時間箱才算對 — 使用者要求的嚴格版)
  Hits@3/@10   : rank < 3 / 10
  mean_rank    : mean(rank) + 1 (1-based for readability; the original script
                 prints the 0-based mean, recorded as mean_rank_0based)
Usage: hyte_time_metrics.py <year|month> <mode> <test_workdir> <run_name>
                            <best_epoch> <ckpt_match> <sel_mean_rank_0based>
"""
import json, pathlib, subprocess, sys
import numpy as np

gran, mode, workdir, name, best, match, selrank = sys.argv[1:8]
ROOT = pathlib.Path(__file__).resolve().parents[2]
W = pathlib.Path(workdir)
d = W / "temp_scope" / name

gold = [tuple(map(int, l.split())) for l in (d / "valid.txt").read_text().splitlines()]
ranks = []
n_bins = None
with open(d / f"valid_time_pred_{best}.txt") as f:
    for i, line in enumerate(f):
        scores = np.fromstring(line, sep=" ")
        if n_bins is None:
            n_bins = len(scores)   # scope feed = time_steps -> exactly n_bins scores
        order = np.argsort(scores, kind="stable")                # ascending, as original
        pos = {b: p for p, b in enumerate(order)}
        s, e = gold[i]
        ranks.append(min(pos[b] for b in range(s, e + 1)))
r = np.array(ranks, dtype=float)

meta = {}
tm = W / "data" / "yago" / "large" / "time_map.json"
if tm.exists():
    meta = json.loads(tm.read_text())

REPO = ROOT / "repos" / "HyTE"
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                       capture_output=True, text=True).stdout.strip()
dirty = "\n".join(l for l in dirty.splitlines()
                  if "__pycache__" not in l and not l.endswith(".pyc"))

out = {
    "method": "HYTE-time(scoping)", "dataset": f"finreflect_{gran}", "mode": mode,
    "task": "time prediction (temporal scoping)",
    "strict_top1": float(np.mean(r < 1)),
    "Hits@3": float(np.mean(r < 3)), "Hits@10": float(np.mean(r < 10)),
    "mean_rank": float(np.mean(r) + 1), "mean_rank_0based": float(np.mean(r)),
    "n_time_bins": n_bins, "n_eval": len(ranks),
    "best_valid_epoch": int(best),
    "sel_valid_mean_rank_0based": float(selrank),
    "twin_ckpt_bytes_match": match == "true",
    "eval_protocol": "HyTE original time_proj_tdns_scope.py dumps + result_eval_time.py "
                     "rank definition; strict = exact gold time-bin at top-1 (unfiltered). "
                     "Test scores via twin run (valid.txt=test split) with identical "
                     "args+seed; epoch selected on the real valid split.",
    "repo": "github.com/malllabiisc/HyTE", "repo_commit": commit,
    "repo_diff": dirty or "CLEAN (zero modification)",
    "entry_point": f"python time_proj_tdns_scope.py -name scope_{gran}_* ... "
                   f"(see runs/hyte_scope_{gran}.log)",
    "data_meta": meta,
    "notes": "class space = HyTE's own frequency bins (hardcoded >300 count), not raw "
             "years/months; year vs month variants differ in token granularity feeding "
             "that binning.",
}
res = ROOT / "results"; res.mkdir(exist_ok=True)
(res / f"hyte_time_finreflect_{gran}.json").write_text(json.dumps(out, indent=2))
print(json.dumps({k: out[k] for k in ("dataset", "strict_top1", "Hits@3", "Hits@10",
                                      "mean_rank", "n_time_bins", "best_valid_epoch",
                                      "twin_ckpt_bytes_match")}, indent=2))
