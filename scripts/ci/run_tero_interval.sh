#!/usr/bin/env bash
# TeRo (ATISE repo, 原碼零改) — FinReflect 區間版：走 yago 路徑(Dataset_YG)讀 start/end 兩個時間，
# 並以 --timedisc 1 啟動對偶關係(begin↔r, end↔dual-r)。資料由 converters/to_tero_interval.py 產生。
# 用法: run_tero_interval.sh <smoke|full>
set -euo pipefail
MODE="${1:-full}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="$ROOT/repos/ATISE"
WORK="$ROOT/data_ready/tero_interval/finreflect"     # 內含 yago/ 子目錄
EPOCHS=$([ "$MODE" = smoke ] && echo 250 || echo 5000)
mkdir -p "$ROOT/runs"; LOG="$ROOT/runs/tero_interval_finreflect.log"
cd "$WORK"; rm -rf yago/TERO
CMD=(python "$REPO/Main.py" --dataset yago --model TERO --dim 500 --lr 0.1 --gamma 110
     --loss logloss --timedisc 1 --cuda "" --thre 1 --max_epoch "$EPOCHS")
echo "CMD: ${CMD[*]}" | tee "$LOG"
PYTHONUNBUFFERED=1 PYTHONPATH="$REPO" "${CMD[@]}" 2>&1 | tee -a "$LOG"
python "$ROOT/scripts/ci/parse_atise.py" tero_interval finreflect "$MODE" || \
  echo "（解析器需加 tero_interval 分支；見 INTERVAL_ABLATION.md）"
