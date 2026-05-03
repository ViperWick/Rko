# eToro — 從這裡啟動（所有 .bat 都在這裡）

**懶得看細節？** → 直接打開 **`../docs/簡易操作流程.md`**（只有一頁）。

**所有類型的 AI Agent 統一入口** → repo 根目錄 **`ai_agents/`**（選單與捷徑說明見該資料夾 `README.md`）。

**本資料夾 `etoro_trading/啟動檔/`** 放 **eToro / Streamlit / 日常排程** 等雙擊檔（與 `ai_agents` 裡 eToro 啟動器行為相同者可擇一使用）。  
金鑰放在：**`etoro_trading/.env`**

---

## 我想做什麼 → 雙擊哪個？

| 我想… | 雙擊 |
|--------|------|
| **瀏覽器主程式（完整功能，需 API）** | `run_ui.bat` |
| **簡易展示頁（不需金鑰，給人看介面）** | `run_ui_demo.bat` |
| **輔助工具選單**（匯出持倉、量子 Excel、整合表…） | `run_scripts_menu.bat` |
| **只要今天的 Markdown 總結** | `run_today_summary.bat` |
| **連線並把持倉寫入文字檔**（輸出在 `data/portfolio_output.txt`） | `run_portfolio.bat` |
| **一次跑完多個日常腳本 + 寫 log**（可搭配工作排程器每天自動） | `run_daily_automation.bat` → 見 **`../docs/日常自動化_排程說明.md`** |
| **本機 Ollama 摘要最新自動化 log**（一鍵、等同選單 20） | `一鍵_Ollama摘要.bat` → 詳見 **`../docs/Ollama_本機摘要設定.md`** |
| **語音監聽**：說「執行摘要」等即跑摘要（視窗需常駐，Ctrl+C 結束） | `啟動_語音摘要監聽.bat` → 詳見 **`../docs/Ollama_本機摘要設定.md`** |

---

## 程式碼放哪？（不再散在根目錄）

| 資料夾 | 說明 |
|--------|------|
| `../core/` | API、持倉、交易、策略、風險、CLI |
| `../signals/` | 均線、RSI、波動等訊號 |
| `../ui/` | Streamlit、`ppt_images/` |
| `../scripts/` | 輔助腳本（`py -m etoro_trading.scripts`） |
| `../data/`、`../docs/` | 資料與文件 |

---

## 若雙擊沒反應

在 **Cursor 終端**、**repo 根目錄** 試：

```bash
cd C:\Users\User\.cursor-tutor
py -m etoro_trading portfolio
```

---

## 本機 Ollama 摘要排程 log（可選）

已安裝 Ollama 時：**雙擊 `一鍵_Ollama摘要.bat`**，或在 repo 根目錄：`py -m etoro_trading.scripts ollama-summarize`  
語音觸發：`py -m etoro_trading.scripts listen-ollama-summarize`（需額外套件，見文件）  
說明：**`../docs/Ollama_本機摘要設定.md`**

---

## 用 Cursor 跟我討論、不必自己找檔

- **帳戶畫面**：用上面的 `run_ui.bat`。
- **問我持倉／數字／策略**：在 Cursor 對話直接說即可；我會依規則幫你跑指令或讀 `data/`。  
  說明：**`../docs/AI對話時資料從哪來.md`**、`../docs/如何用_Cursor_當策略討論_AI_agent.md`。

---

## 進階（終端機）

| 用途 | 指令（repo 根目錄） |
|------|---------------------|
| 主程式 | `py -m etoro_trading --help` |
| 輔助腳本 | `py -m etoro_trading.scripts --help` |

完整說明：**`../README.md`**
