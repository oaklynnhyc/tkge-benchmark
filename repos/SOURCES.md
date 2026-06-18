# repos/ —— 原始方法來源（method repos）

本資料夾用來放**三個原始作者的 repo**（clone 下來、保持原樣）。
repo 內容本身**不納入版本庫**（見根目錄 `.gitignore`），只保留本說明檔。
一鍵取得：在專案根目錄執行 `bash scripts/clone_repos.sh`。

| 目標方法 | 子資料夾 | 來源 URL | 備註 |
|---|---|---|---|
| **ATiSE + TeRo** | `repos/ATISE` | https://github.com/soledad921/ATISE | 同一 repo，執行時用 `--model` 切換 ATiSE / TeRo（PyTorch） |
| **TIMEPLEX** | `repos/tkbi` | https://github.com/dair-iitd/tkbi | PyTorch |
| **HyTE** | `repos/HyTE` | https://github.com/malllabiisc/HyTE | TensorFlow 1.x，環境最舊，建議最後做 |

> clone 後請把各 repo 的 commit hash 記到 `../CHANGELOG.md`，以鎖定「我用的是哪一版原碼」。
