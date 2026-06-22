#!/usr/bin/env bash
# TIMEPLEX (tkbi, 原碼零改) — FinReflect 區間版：別名 WIKIDATA12k 走年級區間路徑，
# --bin_time 1 觸發 use_time_interval、--filter_method time-interval 做區間過濾/評估。
# 資料由 converters/to_timeplex_interval.py 產生。用法: run_timeplex_interval.sh <smoke|full>
set -euo pipefail
MODE="${1:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="$ROOT/repos/tkbi"
WORK="$ROOT/data_ready/timeplex_interval"
EPOCHS=$([ "$MODE" = smoke ] && echo 20 || echo 250)
X=$([ "$MODE" = smoke ] && echo 20 || echo 100)
cd "$WORK"; ln -sfn . data; rm -rf models/WIKIDATA12k_tp_interval logs
mkdir -p "$ROOT/runs"; LOG="$ROOT/runs/timeplex_interval_finreflect.log"
CMD=(python "$REPO/main.py" -d WIKIDATA12k --data_repository_root ./data -m TimePlex_base
  -a '{"embedding_dim":200,"srt_wt":5.0,"ort_wt":5.0,"sot_wt":5.0,"time_reg_wt":1.0,"emb_reg_wt":0.005}'
  -l crossentropy_loss_AllNeg -r 0.1 -b 1000 -x "$X" -n 0 -v 1 -q 0 -y 500 -g_reg 2 -g 1.0
  --bin_time 1 --filter_method time-interval -e "$EPOCHS" --flag_add_reverse 1
  --save_dir models/WIKIDATA12k_tp_interval)
echo "CMD: ${CMD[*]}" | tee "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${CMD[@]}" 2>&1 | tee -a "$LOG" | tail -200
python "$ROOT/scripts/ci/parse_timeplex.py" finreflect "$MODE" interval
