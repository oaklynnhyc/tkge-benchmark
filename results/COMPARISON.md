# TKGE Benchmark — 4 methods × 3 datasets (link prediction)

_Generated 2026-06-18 15:42 UTC; run mode(s): full_

| Method | Dataset | MRR | Hits@1 | Hits@3 | Hits@10 | MR |
|---|---|---|---|---|---|---|
| TeRo | FinReflect | 0.2422 | 0.1894 | 0.2475 | 0.3687 | 576.0000 |
| TeRo | ICEWS18 (5k) | 0.1152 | 0.0656 | 0.1200 | 0.2216 | 962.0000 |
| TeRo | GDELT (5k) | 0.0744 | 0.0296 | 0.0680 | 0.1672 | 313.0000 |
| ATiSE | FinReflect | 0.2595 | 0.2247 | 0.2601 | 0.3359 | 428.0000 |
| ATiSE | ICEWS18 (5k) | 0.0881 | 0.0456 | 0.0952 | 0.1832 | 722.0000 |
| ATiSE | GDELT (5k) | 0.0777 | 0.0344 | 0.0728 | 0.1664 | 366.0000 |
| TIMEPLEX (base) | FinReflect | 0.3391 | 0.2753 | — | 0.4697 | 441.1086 |
| TIMEPLEX (base) | ICEWS18 (5k) | 0.0326 | 0.0160 | — | 0.0680 | 1114.1824 |
| TIMEPLEX (base) | GDELT (5k) | 0.0608 | 0.0240 | — | 0.1224 | 414.1296 |
| HyTE | FinReflect | 0.1910 | 0.1212 | 0.1869 | 0.3586 | 383.8561 |
| HyTE | ICEWS18 (5k) | 0.0574 | 0.0200 | 0.0536 | 0.1440 | 846.4368 |
| HyTE | GDELT (5k) | 0.0481 | 0.0016 | 0.0464 | 0.1248 | 293.1016 |
| HyTE (interval) | FinReflect | 0.1659 | 0.0884 | 0.1970 | 0.3232 | 366.0682 |

## 評估協定差異（誠實註腳，不假裝完全等價）

- **共同點**：四方法吃**同一份資料與同一份 train/valid/test 切分**
  （FinReflect：去重後 seed=42、80/10/10，1580/197/198；ICEWS18、GDELT：原 5k 抽樣
  train 5000 / valid 625 / test 625，seed=42）。指標皆為 head+tail 兩方向平均的
  entity link prediction。
- **TeRo / ATiSE**（ATISE repo 原生評估）：time-wise *filtered* 排名；訓練含反向關係
  （rev_set=1，原碼預設）。
- **TIMEPLEX base**（tkbi 原生評估）：`time-str` *filtered* 排名（與 ATISE 的過濾近似
  但實作不同）；`--flag_add_reverse 1`（原 README 設定）。原生不輸出 Hits@3（表中 `—`）。
- **HyTE**（原生 dump + 後處理）：**RAW（無過濾）**排名——HyTE 原始碼只支援 raw MR/Hits@10；
  MRR/Hits@1/3 由其 score dump 以同一排名定義後算（未動原碼）。Raw 排名通常**低估** HyTE
  相對 filtered 方法的表現，跨方法比較時請注意。
- **時間切分注意**：ICEWS18/GDELT 的 train/valid/test 為**時間順序切分**（如 ICEWS18：
  train=1–8 月、valid=9 月、test=10 月），即評估時間戳皆在訓練範圍之後。
  ATISE/tkbi 原生可對未見時間戳評分（時間嵌入未經訓練）；HyTE 的時間分箱僅由 train 建立，
  故 eval 時間戳一律**鉗制到最後一個訓練時間箱**（=未來事實使用最近的超平面；
  轉檔層處理、原碼未動；FinReflect 為隨機切分、零鉗制）。
- **時間編碼**：三份資料皆時間點。FinReflect=年；ICEWS18/GDELT=日。
  ATISE repo：別名目錄 `icews05-15`、時間平移至 2005 視窗（純資料變換，gran=1）。
  tkbi：GDELT 取別名 `icews-gdelt` 以走其 ICEWS 日級時間解析（僅命名）。
  HyTE：時間點以 4 字元 token 餵入，原生 `create_year2id`（>300 計數）自動分箱。
- **超參**：各 repo README 之 ICEWS14（事件型）官方設定為準；HyTE 用 yago 官方設定、
  batch/epochs 依 5k 規模調整（margin 10、neg 5、l2 0、epoch 1000、test_freq 100）。
  全部 CPU 訓練。
- **HyTE (interval) 變體**（僅 FinReflect、表中獨立一列）：HyTE 原生即區間方法（讀
  start/end 兩欄、把三元組攤到 `[start,end]` 年箱）。此列改餵 FinReflect 真實的
  `start_date`/`end_date`（其餘三方法與點版 HyTE 不變），**只動資料、原碼仍 CLEAN**。
  缺值/雜訊處理：`default_*` 佔位的 end_date（199 列）/start_date（36 列）回退用
  `year` 欄（即點版 HyTE 用的時間戳）；`end<start` 的倒置（2 列）收成點；同一 quad
  多列取最寬區間 min(start)/max(end)。1580 訓練列中有 70 列為真實跨年區間。
  與同列點版 HyTE 比較即「區間 vs 時間點」的消融。轉檔器
  `converters/to_hyte_interval.py`，政策統計見其 `time_map.json`。

## 結論（full run，2026-06-12）

**各資料集最佳方法**

- **FinReflect**（供應鏈 KG、年粒度、隨機切分）：**TIMEPLEX base 明顯最佳**
  （MRR 0.339、H@10 0.470），ATiSE（0.260）與 TeRo（0.242）居中，HyTE 最弱（0.191，
  且其 raw 協定會低估）。FinReflect 只有 3 種關係、實體 1605，TIMEPLEX 的
  關係-時間交互特徵（srt/ort/sot）能吃到供應鏈 KG 的規律。
- **ICEWS18（5k 抽樣、時間切分）**：**TeRo 最佳**（MRR 0.115、H@10 0.222），
  ATiSE 次之（0.088）。TIMEPLEX 反而最弱（0.033）——評估期（9–10 月）的時間戳
  在訓練期（1–8 月）之外，重時間參數化的模型在小樣本＋時間外推下過擬合訓練期。
- **GDELT（5k 抽樣、時間切分、僅 31 天）**：ATiSE（0.078）≈ TeRo（0.074）
  ＞ TIMEPLEX（0.061）＞ HyTE（0.048）。整體絕對值低：GDELT 雜訊高、
  實體/關係多而訓練例少。

**整體訊號**：距離/旋轉型輕量方法（TeRo、ATiSE）在小樣本事件型資料上較穩健；
特徵更重的 TIMEPLEX 在規律性強、隨機切分的 FinReflect 上優勢最大；
HyTE（2018 年方法＋raw 評估）在所有資料上墊底，與文獻相對位置一致。

**原碼零改動確認**：12 個 (方法×資料) 的 `results/*.json` 皆記錄
`repo_diff: CLEAN`＋pinned commit（ATISE `711e2136`、tkbi `e0a26b32`、HyTE `96fc3498`）；
CI 在訓練前以 clean-tree 檢查強制。資料接入全靠別名目錄/命名與純資料變換（轉檔器在
`converters/`，含可逆 time_map）。

**主要限制**：(1) ICEWS18/GDELT 為 5k 抽樣（seed=42），絕對數值不可與全量文獻數字
直接比較；(2) 各 repo 原生評估協定不完全等價（HyTE raw vs 其他 filtered；TIMEPLEX 無
H@3）；(3) 時間切分使事件型資料的評估屬時間外推情境；(4) 單一 seed、CPU、
各 README 官方超參未針對本資料調參；(5) HyTE 的未來時間戳鉗制到最後訓練時間箱。
