#!/usr/bin/env bash
# Clone the original method repos PINNED to the commits recorded for this
# benchmark (proof of unmodified upstream code). Usage: pin_repos.sh [atise|tkbi|hyte ...]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$HERE/repos"
cd "$HERE/repos"

declare -A URL=(
  [atise]="https://github.com/soledad921/ATISE.git"
  [tkbi]="https://github.com/dair-iitd/tkbi.git"
  [hyte]="https://github.com/malllabiisc/HyTE.git"
)
declare -A DIR=( [atise]=ATISE [tkbi]=tkbi [hyte]=HyTE )
declare -A PIN=(
  [atise]=711e2136e10b54acbdd7a69ad7822837ce5c44c8
  [tkbi]=e0a26b32e22ca49957951b0ea0da9b4dc45049a8
  [hyte]=96fc3498d3f3fbc7acd61d81a704537b239ac94d
)

for key in "${@:-atise tkbi hyte}"; do
  d="${DIR[$key]}"; u="${URL[$key]}"; p="${PIN[$key]}"
  if [ ! -d "$d/.git" ]; then git clone --quiet "$u" "$d"; fi
  git -C "$d" checkout --quiet "$p"
  echo "$d @ $(git -C "$d" rev-parse HEAD)"
  # zero-modification proof: working tree must be clean
  if [ -n "$(git -C "$d" status --porcelain)" ]; then
    echo "ERROR: $d working tree not clean (original code modified?)" >&2
    git -C "$d" status --porcelain >&2
    exit 1
  fi
done
