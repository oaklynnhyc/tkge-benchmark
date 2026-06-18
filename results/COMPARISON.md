# TKGE Benchmark — 4 methods × 3 datasets (link prediction)

_Generated 2026-06-18 16:07 UTC; run mode(s): full_

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
| HyTE | ICEWS18 (5k) | 0.0574 | 0.0200 | 0.0536 | 0.1440 | 846.4368 |
| HyTE | GDELT (5k) | 0.0481 | 0.0016 | 0.0464 | 0.1248 | 293.1016 |
| HyTE | FinReflect(interval) | 0.1659 | 0.0884 | 0.1970 | 0.3232 | 366.0682 |

---
- **TIMEPLEX base**（tkbi 原生評估）：`time-str` *filtered* 排名（與 ATISE 的過濾近似
  但實作不同）；`--flag_add_reverse 1`（原 README 設定）。原生不輸出 Hits@3（表中 `—`）。
