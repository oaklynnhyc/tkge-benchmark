# CHANGELOG — tkge-benchmark

記錄重大修改、原始 repo 的鎖定版本、以及每次實驗結果。
慣例：每個里程碑一條，附對應 git commit 短 hash。日期用 `YYYY-MM-DD`。

格式分三區：① 原始 repo 版本鎖定 ② 變更紀錄 ③ 實驗結果索引。

---

## ① 原始方法 repo 鎖定版本（clone 後填入 commit hash）

| 方法 | repo | clone 日期 | commit hash | 原碼是否零改動 |
|---|---|---|---|---|
| ATiSE / TeRo | github.com/soledad921/ATISE | 2026-06-12 | `711e2136e10b54acbdd7a69ad7822837ce5c44c8` | ✅（CI 以 clean-tree 檢查強制） |
| TIMEPLEX | github.com/dair-iitd/tkbi | 2026-06-12 | `e0a26b32e22ca49957951b0ea0da9b4dc45049a8` | ✅（CI 以 clean-tree 檢查強制） |
| HyTE | github.com/malllabiisc/HyTE | 2026-06-12 | `96fc3498d3f3fbc7acd61d81a704537b239ac94d` | ✅（CI 以 clean-tree 檢查強制） |

---

## ② 變更紀錄（新到舊）

### 2026-06-18
- `feat(convert)` 新增 **HyTE (interval) 變體**（僅 FinReflect）：改餵真實
  `start_date`/`end_date`（HyTE 原生即讀 start/end 兩欄、攤到 `[start,end]` 年箱），
  **只動資料、原碼仍 CLEAN**。缺值/雜訊政策：`default_*` 佔位 end(199)/start(36) 回退
  `year` 欄、`end<start`(2) 收成點、同 quad 取 min(start)/max(end)；1580 訓練列 70 列為
  真實跨年區間。轉檔器 `converters/to_hyte_interval.py`、runner `run_hyte_interval.sh`、
  `hyte_metrics.py` 加 interval 變體、`aggregate.py` 表中獨立列 + 註腳、CI（benchmark.yml）
  HyTE job 對 finreflect 加跑。與同列點版 HyTE 即「區間 vs 時間點」消融。
- `fix(ci)` `aggregate.py` 重生 COMPARISON.md 時**保留**手寫「## 結論」段（先前 CI 重生會
  覆蓋掉結論）。

### 2026-06-12（完成）
- `exp(all)` **FULL 訓練完成：4 方法 × 3 資料全部產出**（run 27375188787，artifacts 由
  collect workflow 彙整，commit `b2f90af`）。12 個 results JSON 皆 `repo_diff: CLEAN`。
  結論見 `results/COMPARISON.md`。
- `fix(ci)` aggregate 先 rebase 再 add（push 被拒問題）；新增 collect.yml（依 run-id 收
  artifacts）；matrix 組合過濾器。 (`8a837ad`)
- `fix(env/ci)` smoke 三輪除錯：protobuf pin（TF1.15）、HyTE 缺 requests、TIMEPLEX `-x`
  評估頻率隨 5k 縮放、artifact 萬用字元互相覆蓋改逐檔上傳、HyTE 未來時間戳鉗制
  （ICEWS18/GDELT 為時間切分）。 (`0fae6a1`→`a93bb13`)
- `feat(ci)` GitHub Actions 訓練管線（12 jobs 矩陣 + aggregate）。沙箱限制（單指令 ≤45s、
  背景行程被殺、CPU-only）使本機完整訓練不可行，經使用者同意改在 Actions 免費 runner 訓練；
  原碼零改動由 `scripts/ci/pin_repos.sh` 的 pinned-commit + clean-tree 檢查強制。
- `feat(convert)` `to_atise.py`（別名目錄 icews05-15、時間平移 2005 視窗）、
  `to_timeplex.py`（gdelt 別名 icews-gdelt 選 day-level 解析）、
  `to_hyte.py`（data/yago/large 別名、4 字元時間 token、整數 id）——三者皆零改碼接入。
- `feat(data)` FinReflect 標準切分：去重 2000→1975、seed=42、80/10/10（1580/197/198），
  四方法共用（`converters/split_finreflect.py`，已 commit 切分檔）。
- `chore(env)` 沙箱驗證：ATISE 原碼於 icews14 與 finreflect 可訓練（loss 收斂中）；
  tkbi 原碼於 finreflect 可訓練。HyTE 需 TF1.15（CI 以 python:3.7 容器處理）。

### 2026-06-11
- `chore` 專案初始化：data_source（finreflect；icews18/gdelt 5k 抽樣）＋ sampler ＋ docs。 (`75b439f`)
- `docs` 新增方法 repo 來源與 clone 腳本。 (`6354c46`)

<!-- 範例條目，Fable 依此續寫：
### 2026-06-13
- `feat(convert)` finreflect → ATISE 格式轉檔。 (`abc1234`)
- `exp(tero)` finreflect 煙霧測試通過，5 epoch。 (`def5678`)
- `fix(env)` ATISE repo 相依：pin torch==1.x、numpy<2。 (`...`)
-->

---

## ③ 實驗結果索引（指標摘要；完整表見 results/COMPARISON.md）

| 日期 | 方法 | 資料集 | 資料版本 | MRR | H@1 | H@3 | H@10 | commit | 備註 |
|---|---|---|---|---|---|---|---|---|---|
| 2026-06-12 | TeRo | FinReflect | full(2k去重1975) | 0.2422 | 0.1894 | 0.2475 | 0.3687 | `b2f90af` | time-wise filtered |
| 2026-06-12 | TeRo | ICEWS18 | 5k(seed42) | 0.1152 | 0.0656 | 0.1200 | 0.2216 | `b2f90af` | 時間切分外推 |
| 2026-06-12 | TeRo | GDELT | 5k(seed42) | 0.0744 | 0.0296 | 0.0680 | 0.1672 | `b2f90af` | |
| 2026-06-12 | ATiSE | FinReflect | full(2k去重1975) | 0.2595 | 0.2247 | 0.2601 | 0.3359 | `b2f90af` | |
| 2026-06-12 | ATiSE | ICEWS18 | 5k(seed42) | 0.0881 | 0.0456 | 0.0952 | 0.1832 | `b2f90af` | |
| 2026-06-12 | ATiSE | GDELT | 5k(seed42) | 0.0777 | 0.0344 | 0.0728 | 0.1664 | `b2f90af` | |
| 2026-06-12 | TIMEPLEX | FinReflect | full(2k去重1975) | 0.3391 | 0.2753 | — | 0.4697 | `b2f90af` | 原生無 H@3 |
| 2026-06-12 | TIMEPLEX | ICEWS18 | 5k(seed42) | 0.0326 | 0.0160 | — | 0.0680 | `b2f90af` | |
| 2026-06-12 | TIMEPLEX | GDELT | 5k(seed42) | 0.0608 | 0.0240 | — | 0.1224 | `b2f90af` | |
| 2026-06-12 | HyTE | FinReflect | full(2k去重1975) | 0.1910 | 0.1212 | 0.1869 | 0.3586 | `b2f90af` | RAW（未過濾） |
| 2026-06-12 | HyTE | ICEWS18 | 5k(seed42) | 0.0574 | 0.0200 | 0.0536 | 0.1440 | `b2f90af` | eval 時間戳鉗制 |
| 2026-06-12 | HyTE | GDELT | 5k(seed42) | 0.0481 | 0.0016 | 0.0464 | 0.1248 | `b2f90af` | eval 時間戳鉗制 |

> 註：各 repo 原生評估協定若有差異（如 HyTE 的過濾方式），在此欄與 COMPARISON.md 標明。
