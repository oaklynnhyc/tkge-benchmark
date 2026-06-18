#!/usr/bin/env bash
# Run HyTE (original repo, TF1.x, UNMODIFIED) on FinReflect using its REAL time
# INTERVAL (start_date/end_date) — the interval variant. HyTE is natively an
# interval method (reads cols [3],[4] as start/end), so this is a pure data
# change: converters/to_hyte_interval.py writes real start!=end years; no repo
# file is touched. FinReflect only.
# Usage: run_hyte_interval.sh <smoke|full>
set -euo pipefail
DS="finreflect"; MODE="${1:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="$ROOT/repos/HyTE"
WORK="$ROOT/data_ready/hyte_interval/$DS"
NAME="hyte_interval_${DS}"

if [ "$MODE" = smoke ]; then EPOCHS=100; FREQ=50; else EPOCHS=1000; FREQ=100; fi
BATCH=2500

cd "$WORK"
rm -rf checkpoints results tf_board logs "$NAME"
mkdir -p "$ROOT/runs"
LOG="$ROOT/runs/${NAME}.log"

# Identical hyperparams to the point-HyTE run (run_hyte.sh) so the only
# difference is point vs real interval; -gpu '' => CPU.
TRAIN=(python "$REPO/time_proj.py" -name "$NAME" -margin 10 -l2 0.00
       -neg_sample 5 -gpu '' -epoch "$EPOCHS" -test_freq "$FREQ"
       -batch "$BATCH" -data_type yago -version large)
echo "CMD: ${TRAIN[*]}" | tee "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${TRAIN[@]}" 2>&1 | tee -a "$LOG" | tail -40

set +e
EVAL_OUT=$(PYTHONPATH="$REPO" python "$REPO/result_eval.py" \
            -eval_mode valid -model "$NAME" -test_freq "$FREQ" 2>/dev/null)
set -e
echo "$EVAL_OUT" | tee -a "$LOG"
BEST=$(echo "$EVAL_OUT" | grep -o "Best Validation Epoch till now Epoch [0-9]*" | tail -1 | grep -o "[0-9]*$")
echo "BEST_VALID_EPOCH=$BEST" | tee -a "$LOG"

TEST=(python "$REPO/time_proj.py" -res_epoch "$BEST" -onlyTest -restore
      -name "$NAME" -margin 10 -l2 0.00 -neg_sample 5 -gpu ''
      -batch "$BATCH" -data_type yago -version large)
echo "CMD: ${TEST[*]}" | tee -a "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${TEST[@]}" 2>&1 | tee -a "$LOG" | tail -20

python "$ROOT/scripts/ci/hyte_metrics.py" "$DS" "$MODE" "$NAME" "$BEST" interval
