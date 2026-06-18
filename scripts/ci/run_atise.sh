#!/usr/bin/env bash
# Run TeRo / ATiSE (original ATISE repo entry point, unmodified) on one dataset.
# Usage: run_atise.sh <tero|atise> <finreflect|icews18|gdelt> <smoke|full>
# The dataset is presented to the original code under the alias directory
# 'icews05-15' (hardcoded start_date=2005-01-01, n_time=4017) from its own
# working dir; timestamps were shifted into that window by converters/to_atise.py.
set -euo pipefail
METHOD="$1"; DS="$2"; MODE="${3:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$ROOT/data_ready/atise/$DS"
REPO="$ROOT/repos/ATISE"

MODEL=$([ "$METHOD" = tero ] && echo TERO || echo ATISE)
EPOCHS=$([ "$MODE" = smoke ] && echo 250 || echo 5000)

# Original README icews14 commands, CPU (--cuda "" -> argparse bool False),
# gran=1 (pure time-point data), max_epoch per mode.
if [ "$MODEL" = TERO ]; then
  ARGS=(--model TERO --dim 500 --lr 0.1 --gamma 110 --loss logloss --eta 10
        --timedisc 0 --cuda "" --gran 1 --max_epoch "$EPOCHS")
else
  ARGS=(--model ATISE --dim 500 --lr 0.00003 --gamma 120 --loss logloss
        --timedisc 0 --cuda "" --gran 1 --cmin 0.003 --max_epoch "$EPOCHS")
fi

mkdir -p "$ROOT/runs"
LOG="$ROOT/runs/${METHOD}_${DS}.log"
cd "$WORK"
rm -rf "icews05-15/$MODEL"   # original code aborts if output path exists
echo "CMD: python Main.py --dataset icews05-15 ${ARGS[*]}" | tee "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" python "$REPO/Main.py" \
  --dataset icews05-15 "${ARGS[@]}" 2>&1 | tee -a "$LOG"

python "$ROOT/scripts/ci/parse_atise.py" "$METHOD" "$DS" "$MODE"
