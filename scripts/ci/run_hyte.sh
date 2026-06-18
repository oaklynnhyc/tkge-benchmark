#!/usr/bin/env bash
# Run HyTE (original repo, TF1.x, unmodified) on one dataset.
# Usage: run_hyte.sh <finreflect|icews18|gdelt> <smoke|full>
# Original code hardcodes data/yago/large/ paths -> we run from a per-dataset
# working dir that contains our converted data under that alias (no code change).
set -euo pipefail
DS="$1"; MODE="${2:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="$ROOT/repos/HyTE"
WORK="$ROOT/data_ready/hyte/$DS"
NAME="hyte_${DS}"

if [ "$MODE" = smoke ]; then EPOCHS=100; FREQ=50; else EPOCHS=1000; FREQ=100; fi
BATCH=2500

cd "$WORK"
rm -rf checkpoints results tf_board logs "$NAME"
mkdir -p "$ROOT/runs"
LOG="$ROOT/runs/hyte_${DS}.log"

# Original entry point; paper-style hyperparams (yago command) except
# batch/epochs sized for the 5k benchmark; -gpu '' => CPU.
TRAIN=(python "$REPO/time_proj.py" -name "$NAME" -margin 10 -l2 0.00
       -neg_sample 5 -gpu '' -epoch "$EPOCHS" -test_freq "$FREQ"
       -batch "$BATCH" -data_type yago -version large)
echo "CMD: ${TRAIN[*]}" | tee "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${TRAIN[@]}" 2>&1 | tee -a "$LOG" | tail -40

# Best validation epoch via the ORIGINAL result_eval.py (it crashes at the
# first missing dump file by design; we keep its last printed best epoch).
set +e
EVAL_OUT=$(PYTHONPATH="$REPO" python "$REPO/result_eval.py" \
            -eval_mode valid -model "$NAME" -test_freq "$FREQ" 2>/dev/null)
set -e
echo "$EVAL_OUT" | tee -a "$LOG"
BEST=$(echo "$EVAL_OUT" | grep -o "Best Validation Epoch till now Epoch [0-9]*" | tail -1 | grep -o "[0-9]*$")
echo "BEST_VALID_EPOCH=$BEST" | tee -a "$LOG"

# Restore best weights and dump test predictions (original flow).
TEST=(python "$REPO/time_proj.py" -res_epoch "$BEST" -onlyTest -restore
      -name "$NAME" -margin 10 -l2 0.00 -neg_sample 5 -gpu ''
      -batch "$BATCH" -data_type yago -version large)
echo "CMD: ${TEST[*]}" | tee -a "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${TEST[@]}" 2>&1 | tee -a "$LOG" | tail -20

python "$ROOT/scripts/ci/hyte_metrics.py" "$DS" "$MODE" "$NAME" "$BEST"
