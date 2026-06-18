#!/usr/bin/env bash
# 將三個原始方法 repo clone 進 repos/（保持原樣，不納入本專案版本庫）。
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HERE/repos"
cd "$HERE/repos"

clone() {  # $1=url  $2=dir  $3=note
  if [ -d "$2/.git" ]; then
    echo "[skip] $2 已存在"
  else
    echo "[clone] $3 -> $2"
    git clone "$1" "$2"
  fi
  echo -n "       $2 @ "; git -C "$2" rev-parse --short HEAD
}

clone https://github.com/soledad921/ATISE.git ATISE "ATiSE + TeRo"
clone https://github.com/dair-iitd/tkbi.git   tkbi  "TIMEPLEX"
clone https://github.com/malllabiisc/HyTE.git HyTE  "HyTE (TF1.x)"

echo
echo "完成。請把上面各 commit hash 記到 CHANGELOG.md。"
