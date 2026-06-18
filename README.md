# tkge-benchmark

獨立對比實驗：以**原作者 repo 的方法本體**（零改碼）跑四個 TKGE 方法 ×三份時間點型資料的
連結預測（MRR / Hits@1/3/10）。最終對比表：[`results/COMPARISON.md`](results/COMPARISON.md)。

| 方法 | 原始 repo（pinned commit 見 CHANGELOG）| 框架 |
|---|---|---|
| TeRo / ATiSE | github.com/soledad921/ATISE | PyTorch |
| TIMEPLEX (base) | github.com/dair-iitd/tkbi | PyTorch |
| HyTE | github.com/malllabiisc/HyTE | TensorFlow 1.15 |

資料（`data_source/`，皆含時間欄）：FinReflect（供應鏈 KG，年粒度，去重後 1975 筆，
seed=42 80/10/10 切分）；ICEWS18、GDELT（皆 5k 抽樣 train5000/valid625/test625、seed=42，日粒度）。

## 設計原則：用原作者方法，只動資料

任何方法的模型／評分／訓練核心未改（CI 對 pinned commit 做 clean-tree 檢查）。
新資料集以「別名」接入各 repo 的硬編碼路徑/名稱：

- **ATISE**：資料擺進 `data_ready/atise/<ds>/icews05-15/`，以該別名目錄為 cwd 執行原始
  `Main.py`；時間平移映射到 2005 視窗（純資料變換，`time_map.json` 可逆）。
- **tkbi**：`--data_repository_root` 指向轉檔資料；GDELT 取名 `icews-gdelt` 以選取其
  ICEWS 日級時間解析路徑（純命名）。
- **HyTE**：資料擺進 `data_ready/hyte/<ds>/data/yago/large/`（其硬編碼路徑），時間點以
  4 字元 token 餵入、由其原生分箱處理。

## 如何重現

```bash
bash scripts/ci/pin_repos.sh            # 取得三個原始 repo（鎖定 commit）
python converters/split_finreflect.py   # （已 commit，可重現）
python converters/to_atise.py && python converters/to_timeplex.py && python converters/to_hyte.py
bash scripts/ci/run_atise.sh tero finreflect full   # 其餘 (方法×資料) 同理
```

訓練在 GitHub Actions 上執行（`.github/workflows/benchmark.yml`，workflow_dispatch，
mode=smoke|full）；`aggregate` job 彙整 `results/*.json` 成 `COMPARISON.md` 並 commit 回 main。

評估協定差異（HyTE raw vs 其他 filtered、TIMEPLEX 無 Hits@3 等）詳見
`results/COMPARISON.md` 註腳——不假裝完全等價。
