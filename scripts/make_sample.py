#!/usr/bin/env python3
"""
make_sample.py — 從「已解碼、含時間欄」的 5 欄 TKG 資料抽樣（保留時間），
或一鍵切回完整資料。預設為 GDELT 5000 抽樣。

輸入格式（每個 split 一個檔，可含表頭）:
    subject \t relation \t object \t time_step \t date/datetime

用法:
    # 預設：GDELT 抽 5000 train / 625 valid / 625 test（保留時間欄）
    python scripts/make_sample.py \
        --src ../Methods/FinReflectData_TransE/GDELT_data_decoded \
        --out data_source/gdelt --n-train 5000 --n-eval 625 --seed 42

    # 切回完整資料（不抽樣，整份複製）
    python scripts/make_sample.py --src <DECODED_DIR> --out data_source/gdelt --full

同一支腳本也適用 ICEWS18（格式相同）。
"""
import argparse, csv, json, os, random, sys

SPLIT_FILES = {  # 接受兩種命名
    "train": ["train_decoded.tsv", "train.tsv", "train.txt"],
    "valid": ["valid_decoded.tsv", "valid.tsv", "valid.txt"],
    "test":  ["test_decoded.tsv",  "test.tsv",  "test.txt"],
}

def find_file(src, names):
    for n in names:
        p = os.path.join(src, n)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"在 {src} 找不到任一個: {names}")

def read_rows(path):
    with open(path, encoding="utf-8") as f:
        first = f.readline()
        has_header = first.lower().startswith(("subject", "head"))
        header = first.rstrip("\n") if has_header else None
        rows = [] if has_header else [first.rstrip("\n")]
        for line in f:
            line = line.rstrip("\n")
            if line:
                rows.append(line)
    return header, rows

def write_rows(path, header, rows):
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write(header + "\n")
        f.write("\n".join(rows) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="解碼後資料夾（含 *_decoded.tsv）")
    ap.add_argument("--out", required=True, help="輸出資料夾")
    ap.add_argument("--n-train", type=int, default=5000)
    ap.add_argument("--n-eval", type=int, default=625)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--full", action="store_true", help="不抽樣，整份複製")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    random.seed(args.seed)
    meta = {"mode": "FULL" if args.full else "SAMPLE",
            "src": os.path.abspath(args.src), "seed": args.seed,
            "n_train": None if args.full else args.n_train,
            "n_eval": None if args.full else args.n_eval, "counts": {}}

    targets = {"train": args.n_train, "valid": args.n_eval, "test": args.n_eval}
    for split, names in SPLIT_FILES.items():
        header, rows = read_rows(find_file(args.src, names))
        if not args.full:
            k = min(targets[split], len(rows))
            rows = random.sample(rows, k)
        write_rows(os.path.join(args.out, f"{split}.tsv"), header, rows)
        meta["counts"][split] = len(rows)

    with open(os.path.join(args.out, "sample_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[{meta['mode']}] -> {args.out}  counts={meta['counts']}  seed={args.seed}")

if __name__ == "__main__":
    main()
