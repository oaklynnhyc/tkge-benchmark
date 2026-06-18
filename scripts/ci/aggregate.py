#!/usr/bin/env python3
"""Build results/COMPARISON.md from results/*.json (4 methods x 3 datasets)."""
import json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / "results"
METHODS = [("tero", "TeRo"), ("atise", "ATiSE"),
           ("timeplex", "TIMEPLEX (base)"), ("hyte", "HyTE")]
DATASETS = [("finreflect", "FinReflect"), ("icews18", "ICEWS18 (5k)"),
            ("gdelt", "GDELT (5k)")]

def fmt(v, pct=False):
    if v is None: return "—"
    return f"{v:.4f}"

rows, missing, modes = [], [], set()
for mkey, mname in METHODS:
    for dkey, dname in DATASETS:
        p = RES / f"{mkey}_{dkey}.json"
        if not p.exists():
            missing.append(f"{mname} × {dname}")
            rows.append((mname, dname, None))
            continue
        j = json.loads(p.read_text())
        modes.add(j.get("mode", "?"))
        rows.append((mname, dname, j))

# Interval variant (HyTE only, FinReflect only): appended as its own row so the
# 4x3 point-time matrix above stays unchanged. See footnote.
intv = RES / "hyte_interval_finreflect.json"
if intv.exists():
    rows.append(("HyTE (interval)", "FinReflect", json.loads(intv.read_text())))

lines = []
lines.append("# TKGE Benchmark — 4 methods × 3 datasets (link prediction)\n")
lines.append(f"_Generated {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC; "
             f"run mode(s): {', '.join(sorted(modes)) or 'n/a'}_\n")
lines.append("| Method | Dataset | MRR | Hits@1 | Hits@3 | Hits@10 | MR |")
lines.append("|---|---|---|---|---|---|---|")
for mname, dname, j in rows:
    if j is None:
        lines.append(f"| {mname} | {dname} | — | — | — | — | — |")
        continue
    h1, h3, h10 = j.get("Hits@1"), j.get("Hits@3"), j.get("Hits@10")
    # HyTE post-computed hits are fractions; ATISE native also fractions.
    lines.append(f"| {mname} | {dname} | {fmt(j.get('MRR'))} | {fmt(h1)} | "
                 f"{fmt(h3)} | {fmt(h10)} | {fmt(j.get('MR'))} |")

lines.append("""
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
""")
if missing:
    lines.append("**缺漏（執行失敗或尚未完成）**: " + "; ".join(missing) + "\n")

# Preserve any hand-written conclusions section across regenerations: the
# auto-generated part above ends at the footnote; everything from a '## 結論'
# heading onward is human prose and must survive a CI re-run.
prev_path = RES / "COMPARISON.md"
if prev_path.exists():
    prev = prev_path.read_text()
    idx = prev.find("\n## 結論")
    if idx != -1:
        lines.append(prev[idx + 1:].rstrip() + "\n")

prev_path.write_text("\n".join(lines))
print("\n".join(lines))
