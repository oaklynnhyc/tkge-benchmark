# data_source —— 對比實驗用資料說明

這個資料夾是要 **commit 進 GitHub repo** 給 Fable clone 用的。三份資料都保留**時間欄**（TKGE 方法必須）。

## 內容與大小

| 資料集 | 路徑 | 內容 | 大小 | 是否完整 |
|---|---|---|---|---|
| FinReflect | `finreflect/finreflect_sample2000.tsv` | 供應鏈 KG，2000 列（2014–2024）| 280 KB | ✅ 完整 |
| ICEWS18 | `icews18/{train,valid,test}.tsv` | 事件型 TKG（2018），**5000 抽樣** | 0.5 MB | ⚠️ 抽樣（見下） |
| GDELT | `gdelt/{train,valid,test}.tsv` | 事件型 TKG，**5000 抽樣** | 0.5 MB | ⚠️ 抽樣（見下） |

> ICEWS18 與 GDELT 皆採**相同規格抽樣**：train 5000 / valid 625 / test 625、`seed=42`、保留時間欄，可重現。兩者規格一致，利於對比。
> （GDELT 完整 train 檔 126 MB 超過 GitHub 單檔 100 MB 上限本就無法直接 commit；ICEWS18 為與 GDELT 對齊也採同規格抽樣。FinReflect 本身即 2000 列小集，維持完整。）
> 兩份抽樣皆保留切回完整資料的開關（見下）。

## 欄位格式

- **FinReflect**（5 欄、含表頭）：`entity, relationship, target, year, ...`（關係：produces / operates_in / supplies）。
- **ICEWS18 / GDELT**（5 欄、含表頭）：`subject  relation  object  time_step  date/datetime`（tab 分隔）。
- 三份資料時間皆為**時間點**（無區間）。各資料集已附 train/valid/test 切分，**請沿用、勿重切**。

⚠️ 注意：repo 另一處 `Methods/FinReflectData_TransE/*_transe_5k/` 是**舊的 3 欄（無時間）TransE 版本，不可用於 TKGE**。請一律使用本 `data_source/` 內的檔案。

## GDELT 完整資料 ↔ 5k 抽樣 的切換

抽樣由 `../scripts/make_sample.py` 產生，是可重現的。完整 GDELT 解碼檔在本機（未進 git）：
`AI_SupplyChain_RA/Methods/FinReflectData_TransE/GDELT_data_decoded/`。

```bash
# 重現預設 5k 抽樣（已內含於 repo）
python scripts/make_sample.py \
    --src <完整GDELT解碼夾> --out data_source/gdelt \
    --n-train 5000 --n-eval 625 --seed 42

# 切回完整 GDELT（整份複製，不抽樣）— 會產生 >100MB 檔，勿 commit
python scripts/make_sample.py --src <完整GDELT解碼夾> --out data_source/gdelt --full

# 改抽不同大小（例：1 萬列）
python scripts/make_sample.py --src <完整GDELT解碼夾> --out data_source/gdelt --n-train 10000 --n-eval 1250
```

- `data_source/<ds>/sample_meta.json` 會記錄當前是 SAMPLE 還是 FULL、抽樣大小與 seed，方便追溯結果對應哪一版資料。
- **ICEWS18 也用同一支腳本、同規格抽樣**（已內含於 repo）。重現方式：
  ```bash
  python scripts/make_sample.py --src <完整ICEWS18解碼夾> --out data_source/icews18 \
      --n-train 5000 --n-eval 625 --seed 42
  # 切回完整 ICEWS18（33MB，可進 git 但較重）
  python scripts/make_sample.py --src <完整ICEWS18解碼夾> --out data_source/icews18 --full
  ```
  完整 ICEWS18 解碼檔在本機：`AI_SupplyChain_RA/Methods/FinReflectData_TransE/ICEWS18_data_decoded/`。

## 給 Fable 的提醒

- 預設 **ICEWS18 與 GDELT 皆用 5k 抽樣版**；報告結果時在 `results/COMPARISON.md` 標明為抽樣版（附各自 `sample_meta.json` 的 seed 與列數）。
- 若我要求換完整資料，用上面 `--full` 重生、走 git-lfs 或本機路徑，**不要直接 commit 超過 100MB 的檔**。
