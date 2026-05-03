# AI Agents 統一入口

**完全新手？** 先看 repo 的 **`docs/AI與程式入門_專案架構總覽.md`**（指令、程式觀念、AI 名詞、本專案怎麼拼在一起）。

這個資料夾是 **「今天要開哪一種 AI / Agent」的唯一集散地**。  
裡面只有 **啟動器（.bat）與說明**，**不複製** `etoro_trading`、`local_agent_demo` 的程式碼。

每個 `.bat` 會自動：

1. `cd` 到 **repo 根目錄**（`.cursor-tutor`）
2. 呼叫對應的 `py -m ...` 或腳本路徑

所以 **聽得懂、也找得到** 各專案裡真正的程式。

---

## 怎麼用

| 你想… | 雙擊 |
|--------|------|
| 看選單一次選一個 | **`選單_啟動AI_Agent.bat`** |
| eToro：語音說「執行摘要」等 | **`啟動_eToro_語音摘要監聽.bat`** |
| eToro：直接跑一次 Ollama 摘要 | **`啟動_eToro_Ollama摘要一鍵.bat`** |
| 教學用：local_agent_demo 迴圈 | **`啟動_教學Agent_local_agent_demo.bat`** |
| 只開 Ollama 桌面（選模型聊天） | **`啟動_Ollama桌面程式.bat`** |

---

## 終端機：Claude Code / OpenAI Codex（已用 npm 全域安裝）

若已安裝 **Node.js**，可在 **PowerShell / CMD**（建議**新開**視窗，PATH 才會更新）執行：

| 指令 | 說明 |
|------|------|
| `claude` | Anthropic **Claude Code**（終端機編程助理） |
| `codex` | OpenAI **Codex CLI**（開源 coding agent） |

**費用與帳號：** 兩者實際呼叫模型時通常需 **Anthropic / OpenAI 帳號**（訂閱或 API 金鑰），**不是**本機 Ollama 免費額度。首次執行會引導登入或設定。  
**Windows：** Claude Code 官方建議一併安裝 [**Git for Windows**](https://git-scm.com/download/win)。

Ollama 選單裡的「Launch …」偵測的也是上述 CLI 是否已安裝；安裝後可**關掉再開** Ollama 終端選單試一次。

---

## 與其他資料夾的關係

| 此處啟動器 | 實際跑的是 |
|------------|------------|
| eToro 相關 | `etoro_trading.scripts`（程式在 `etoro_trading/`） |
| 教學 Agent | `local_agent_demo/agent.py`（程式在 `local_agent_demo/`） |
| Ollama 桌面 | 系統安裝的 `Ollama.exe` |

`etoro_trading/啟動檔/` 裡舊的 **`一鍵_Ollama摘要.bat`**、**`啟動_語音摘要監聽.bat`** 仍可照常使用，與這裡行為相同，只是入口多了一個集中資料夾。

---

## Cursor 裡的對話 AI

在 **Cursor 聊天** 不算本機常駐 Agent，無法用 `.bat` 取代；需要討論程式時直接開 Cursor 即可。
