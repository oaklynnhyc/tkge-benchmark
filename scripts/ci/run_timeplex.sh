#!/usr/bin/env bash
# Run TIMEPLEX base (original tkbi repo entry point, unmodified) on one dataset.
# Usage: run_timeplex.sh <finreflect|icews18|gdelt> <smoke|full>
set -euo pipefail
DS="$1"; MODE="${2:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="$ROOT/repos/tkbi"
WORK="$ROOT/data_ready/timeplex"

declare -A ALIAS=( [finreflect]=finreflect [icews18]=icews18 [gdelt]=icews-gdelt )
A="${ALIAS[$DS]}"
EPOCHS=$([ "$MODE" = smoke ] && echo 20 || echo 250)  # smoke: >=20 minibatches so X=20 eval fires
# -x = eval/checkpoint frequency in MINIBATCHES (README icews14 uses 2000 for
# ~36k total minibatches). Scaled to our 5k benchmark so validation actually
# fires: finreflect full ~790 mb, icews18/gdelt full ~2500 mb.
if [ "$MODE" = smoke ]; then X=20   # >=20: trainer does eval_every//20 for its progress bar
elif [ "$DS" = finreflect ]; then X=100
else X=250; fi

cd "$WORK"
ln -sfn . data   # tkbi main.py hardcodes './data/<ds>' for its filter datamap
rm -rf "models/${A}_timeplex_base" logs
mkdir -p "$ROOT/runs"
LOG="$ROOT/runs/timeplex_${DS}.log"

# Original README icews14 TimePlex_base command (CPU auto-detected by the repo).
CMD=(python "$REPO/main.py" -d "$A" --data_repository_root ./data \
  -m TimePlex_base \
  -a '{"embedding_dim":200, "srt_wt": 5.0, "ort_wt": 5.0, "sot_wt": 5.0, "time_reg_wt":1.0, "emb_reg_wt":0.005}' \
  -l crossentropy_loss_AllNeg -r 0.1 -b 1000 -x "$X" -n 0 -v 1 -q 0 -y 500 \
  -g_reg 2 -g 1.0 --filter_method time-str -e "$EPOCHS" --flag_add_reverse 1 \
  --save_dir "models/${A}_timeplex_base")
echo "CMD: ${CMD[*]}" | tee "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${CMD[@]}" 2>&1 | tee -a "$LOG" | tail -200

python "$ROOT/scripts/ci/parse_timeplex.py" "$DS" "$MODE"
