#!/usr/bin/env python3
"""Collect the LAST test_result*.txt produced by the original ATISE Train.py
(early-stop or final-epoch test evaluation) -> results/<method>_<dataset>.json
Usage: parse_atise.py <tero|atise> <dataset> <mode>
"""
import json, pathlib, re, subprocess, sys

method, ds, mode = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = pathlib.Path(__file__).resolve().parents[2]
is_interval = method.endswith("_interval")          # e.g. tero_interval
core = method[:-len("_interval")] if is_interval else method   # tero / atise
model_dir = "TERO" if core == "tero" else "ATISE"
if is_interval:
    # FinReflect 真實區間：走 yago 路徑(Dataset_YG 讀 start/end)，--timedisc 1
    base = ROOT / "data_ready" / f"{core}_interval" / ds / "yago" / model_dir
else:
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

if is_interval:
    proto = ("ATISE repo native (yago path): time-wise filtered; REAL interval "
             "start/end via Dataset_YG; --timedisc 1 dual-relation begin/end")
    entry = (f"python Main.py --dataset yago --model {model_dir} --timedisc 1 "
             f"... (see runs/{method}_{ds}.log)")
    notes = ("FinReflect REAL interval (start/end) fed via ATISE yago path "
             "(Dataset_YG reads cols 4/5); dual-relation begin/end; only data+flag, repo CLEAN")
else:
    proto = "ATISE repo native: time-wise filtered, head+tail averaged"
    entry = ("python Main.py --dataset icews05-15 --model "
             f"{model_dir} ... (see runs/{method}_{ds}.log)")
    notes = "dataset aliased as icews05-15 dir; timestamps shifted to 2005 window (pure data transform)"

out = {
    "method": f"{model_dir}(interval)" if is_interval else method.upper(),
    "dataset": ds, "mode": mode,
    "MRR": metrics.get("Mean RR"), "MR": metrics.get("Mean Rank"),
    "Hits@1": metrics.get("Hit@1"), "Hits@3": metrics.get("Hit@3"),
    "Hits@10": metrics.get("Hit@10"),
    "eval_protocol": proto,
    "test_epoch_file": str(f.relative_to(ROOT)),
    "repo": "github.com/soledad921/ATISE", "repo_commit": commit,
    "repo_diff": dirty or "CLEAN (zero modification)",
    "entry_point": entry,
    "notes": notes,
}
res = ROOT / "results"; res.mkdir(exist_ok=True)
path = res / f"{method}_{ds}.json"
path.write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
