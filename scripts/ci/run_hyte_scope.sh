#!/usr/bin/env bash
# HyTE TIME PREDICTION (temporal scoping) on FinReflect, year|month granularity.
# Original entry points only: time_proj_tdns_scope.py + result_eval_time.py.
# Twin-run protocol (zero code change):
#   run A (_sel dir,  valid.txt = valid split): train, pick best epoch E* by
#          the ORIGINAL result_eval_time.py (min mean time rank);
#   run B (_test dir, valid.txt = test split): identical args + seed -> read
#          its dump at E*. Twin identity verified by checkpoint byte equality.
# Usage: run_hyte_scope.sh <year|month> <smoke|full>
set -euo pipefail
GRAN="$1"; MODE="${2:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="$ROOT/repos/HyTE"

if [ "$MODE" = smoke ]; then EPOCHS=150; FREQ=50; else EPOCHS=1000; FREQ=100; fi
ARGS=(-margin 10 -l2 0.00 -neg_sample 5 -gpu '' -batch 2500 -seed 1234
      -epoch "$EPOCHS" -test_freq "$FREQ" -data_type yago -version large)

mkdir -p "$ROOT/runs"
LOG="$ROOT/runs/hyte_scope_${GRAN}.log"; : > "$LOG"

train_one() {  # $1 = sel|test ; echoes the run's temp_scope dir name
  local W="$ROOT/data_ready/hyte_scope/finreflect_${GRAN}_$1"
  cd "$W"
  rm -rf checkpoints results temp_scope
  echo "CMD[$1]: python time_proj_tdns_scope.py -name scope_${GRAN}_$1 ${ARGS[*]}" >> "$LOG"
  PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" python "$REPO/time_proj_tdns_scope.py" \
      -name "scope_${GRAN}_$1" "${ARGS[@]}" >> "$LOG" 2>&1
  ls temp_scope | head -1
}

NAME_SEL=$(train_one sel)
NAME_TST=$(train_one test)

# --- best epoch via ORIGINAL evaluator (crashes at first missing dump; ok) ---
cd "$ROOT/data_ready/hyte_scope/finreflect_${GRAN}_sel"
mkdir -p results && ln -sfn "$PWD/temp_scope" results/temp_scope
set +e
EV=$(PYTHONPATH="$REPO" python "$REPO/result_eval_time.py" \
       -model "$NAME_SEL" -test_freq "$FREQ" 2>/dev/null)
set -e
echo "$EV" >> "$LOG"
read -r BEST SELRANK <<<"$(echo "$EV" | grep -oE 'Epoch [0-9]+ :  time_rank [0-9.]+' \
  | awk '{print $2, $6}' | sort -k2,2g | head -1)"
echo "BEST_EPOCH=$BEST SEL_MEAN_RANK(0-based)=$SELRANK" | tee -a "$LOG"

# --- twin-identity proof: checkpoint bytes at E* must match ------------------
H1=$(sha256sum "$ROOT/data_ready/hyte_scope/finreflect_${GRAN}_sel/checkpoints/$NAME_SEL/epoch_${BEST}.data-00000-of-00001" | cut -d' ' -f1)
H2=$(sha256sum "$ROOT/data_ready/hyte_scope/finreflect_${GRAN}_test/checkpoints/$NAME_TST/epoch_${BEST}.data-00000-of-00001" | cut -d' ' -f1)
MATCH=$([ "$H1" = "$H2" ] && echo true || echo false)
echo "ckpt sha256 sel=$H1 test=$H2 match=$MATCH" | tee -a "$LOG"

python "$ROOT/scripts/ci/hyte_time_metrics.py" "$GRAN" "$MODE" \
  "$ROOT/data_ready/hyte_scope/finreflect_${GRAN}_test" "$NAME_TST" \
  "$BEST" "$MATCH" "$SELRANK"
