#!/usr/bin/env python3
"""Extract metrics from tkbi's saved best checkpoint (best_valid_model.pt holds
valid/test scores computed by the repo's own evaluate.py).
Usage: parse_timeplex.py <dataset> <mode>
"""
import json, pathlib, subprocess, sys
import torch

ds, mode = sys.argv[1], sys.argv[2]
ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO = ROOT / "repos" / "tkbi"
sys.path.insert(0, str(REPO))  # checkpoint pickles reference repo modules

work = ROOT / "data_ready" / "timeplex"
cands = list(work.rglob("best_valid_model.pt"))
assert cands, f"no best_valid_model.pt under {work}"
ckpt = max(cands, key=lambda p: p.stat().st_mtime)
m = torch.load(ckpt, map_location="cpu")

def f(x):
    try: return float(x)
    except Exception: return None

test, valid = m.get("test_score_m", {}), m.get("valid_score_m", {})
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                       capture_output=True, text=True).stdout.strip()
dirty = "\n".join(l for l in dirty.splitlines()
                  if "__pycache__" not in l and not l.endswith(".pyc"))
out = {
    "method": "TIMEPLEX(base)", "dataset": ds, "mode": mode,
    "MRR": f(test.get("mrr")), "MR": f(test.get("mr")),
    "Hits@1": f(test.get("hits1")), "Hits@3": None,
    "Hits@10": f(test.get("hits10")),
    "valid_MRR": f(valid.get("mrr")),
    "eval_protocol": "tkbi native: time-str filtered, subject+object averaged ('m'); "
                     "repo does not report Hits@3",
    "checkpoint": str(ckpt.relative_to(ROOT)),
    "repo": "github.com/dair-iitd/tkbi", "repo_commit": commit,
    "repo_diff": dirty or "CLEAN (zero modification)",
    "entry_point": f"python main.py -d <alias> -m TimePlex_base ... (see runs/timeplex_{ds}.log)",
    "notes": "gdelt aliased 'icews-gdelt' to select tkbi's day-level ICEWS time parsing (naming only)",
}
res = ROOT / "results"; res.mkdir(exist_ok=True)
(res / f"timeplex_{ds}.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
