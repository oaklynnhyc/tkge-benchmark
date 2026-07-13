#!/usr/bin/env python3
"""Build results/HYTE_YEAR_VS_MONTH.md — HyTE FinReflect year vs month contrast
(entity link prediction + strict time prediction). Reads results/*.json only;
never touches COMPARISON.md."""
import json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / "results"

def load(name):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None

ent_y = load("hyte_finreflect.json")            # existing year baseline (untouched)
ent_m = load("hyte_finreflect_month.json")
tim_y = load("hyte_time_finreflect_year.json")
tim_m = load("hyte_time_finreflect_month.json")

def f(j, k, pct=False):
    if not j or j.get(k) is None: return "—"
    return f"{j[k]:.4f}"

L = []
L.append("# HyTE on FinReflect — 年粒度 vs 月粒度 對照\n")
L.append(f"_Generated {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC_\n")
L.append("兩個變體吃**同一份 train/valid/test 切分、同一組實體/關係 id**，唯一差異是時間欄："
         "年版 token=年（`finreflect`，原始做法，未動）；月版 token=月序"
         "（`finreflect_month`，月份自 start_date join 回，缺月退回一月）。\n")

L.append("## 任務一：Entity link prediction（原 time_proj.py 管線）\n")
L.append("| 變體 | MRR | Hits@1 | Hits@3 | Hits@10 | MR | best epoch | mode |")
L.append("|---|---|---|---|---|---|---|---|")
for tag, j in (("finreflect_year（原基準）", ent_y), ("finreflect_month", ent_m)):
    be = j.get("best_valid_epoch") if j else "—"
    md = j.get("mode") if j else "—"
    L.append(f"| {tag} | {f(j,'MRR')} | {f(j,'Hits@1')} | {f(j,'Hits@3')} | "
             f"{f(j,'Hits@10')} | {f(j,'MR')} | {be} | {md} |")

L.append("\n## 任務二：Time prediction（原 time_proj_tdns_scope.py + result_eval_time.py）\n")
L.append("| 變體 | strict top-1（嚴格版） | Hits@3 | Hits@10 | mean rank | 時間箱數 | best epoch | 雙生run ckpt相符 | mode |")
L.append("|---|---|---|---|---|---|---|---|---|")
for tag, j in (("finreflect_year", tim_y), ("finreflect_month", tim_m)):
    if j:
        L.append(f"| {tag} | {f(j,'strict_top1')} | {f(j,'Hits@3')} | {f(j,'Hits@10')} | "
                 f"{f(j,'mean_rank')} | {j.get('n_time_bins','—')} | {j.get('best_valid_epoch','—')} | "
                 f"{'✅' if j.get('twin_ckpt_bytes_match') else '❌'} | {j.get('mode','—')} |")
    else:
        L.append(f"| {tag} | — | — | — | — | — | — | — | — |")

L.append("""
## 註腳（誠實標註）

- **嚴格版定義**：strict top-1 ＝ 分數最高的時間箱恰為黃金時間箱（時間點資料，
  start=end）才算對；無任何過濾（filtered 版列為後續選項）。排名定義與原
  `result_eval_time.py` 完全一致（分數升冪、取黃金箱位置）。
- **類別空間是 HyTE 自己的分箱**（原碼寫死每箱 >300 計數），不是原始年/月：
  年版與月版各約 10 箱，差別在箱界解析度（月版箱界可切進年中）。
- **資料面**：2000 筆原始列中僅 117 筆 start 月份≠一月（1678 筆為 Jan→Dec 整年
  報告期；格式僅到月，無日）；月版 53 個相異月 token。先驗上月粒度資訊增量有限。
- **test 分數取得**：原 scope 腳本只對 `valid.txt` 檔名評分 → 以「同 seed 雙生 run」
  （valid.txt 分別放驗證集/測試集）取 test 分數；epoch 由驗證集 run 依原始評估器
  （mean time rank 最小）選出；兩 run 模型一致性以 checkpoint 位元組 sha256 驗證
  （上表「雙生run ckpt相符」欄）。
- **entity 任務**與主表 `COMPARISON.md` 的 HyTE 協定相同（RAW 排名、head+tail 平均）。
- 原始碼零改動：兩任務皆用原 repo 進入點；月版僅是新資料目錄（別名載入）。
""")
(RES / "HYTE_YEAR_VS_MONTH.md").write_text("\n".join(L))
print("\n".join(L[:40]))
