#!/usr/bin/env python3
"""Collect the LAST test_result*.txt produced by the original ATISE Train.py
(early-stop or final-epoch test evaluation) -> results/<method>_<dataset>.json
Usage: parse_atise.py <tero|atise> <dataset> <mode>
"""
import json, pathlib, re, subprocess, sys

method, ds, mode = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = pathlib.Path(__file__).resolve().parents[2]
model_dir = "TERO" if method == "tero" else "ATISE"
base = ROOT / "data_ready" / "atise" / ds / "icews05-15" / model_dir

files = sorted(base.rglob("test_result*.txt"),
               key=lambda p: int(re.search(r"(\d+)", p.name).group(1)))
assert files, f"no test_result*.txt under {base}"
f = files[-1]
metrics = {}
for line in f.read_text().splitlines():
    m = re.match(r"(Mean Rank|Mean RR|Hit@1|Hit@3|Hit@5|Hit@10):\s*([\d.]+)", line)
    if m:
        metrics[m.group(1)] = float(m.group(2))

repo = ROOT / "repos" / "ATISE"
commit = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"],
                       capture_output=True, text=True).stdout.strip()
dirty = "\n".join(l for l in dirty.splitlines()
                  if "__pycache__" not in l and not l.endswith(".pyc"))

out = {
    "method": method.upper(), "dataset": ds, "mode": mode,
    "MRR": metrics.get("Mean RR"), "MR": metrics.get("Mean Rank"),
    "Hits@1": metrics.get("Hit@1"), "Hits@3": metrics.get("Hit@3"),
    "Hits@10": metrics.get("Hit@10"),
    "eval_protocol": "ATISE repo native: time-wise filtered, head+tail averaged",
    "test_epoch_file": str(f.relative_to(ROOT)),
    "repo": "github.com/soledad921/ATISE", "repo_commit": commit,
    "repo_diff": dirty or "CLEAN (zero modification)",
    "entry_point": "python Main.py --dataset icews05-15 --model "
                   f"{model_dir} ... (see runs/{method}_{ds}.log)",
    "notes": "dataset aliased as icews05-15 dir; timestamps shifted to 2005 window (pure data transform)",
}
res = ROOT / "results"; res.mkdir(exist_ok=True)
path = res / f"{method}_{ds}.json"
path.write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
