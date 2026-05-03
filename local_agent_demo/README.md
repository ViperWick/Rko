# local_agent_demo — 最小 Agent 框架放哪裡

## 會不會用到付費的 OpenAI？

**不會（照預設設定）。**

- **`pip install openai`** 安裝的是 **開源免費的 Python 函式庫**，只是因為 **Ollama 提供與 OpenAI 相容的 API**，所以用這個庫最省事。
- **`config.py`** 預設 `OLLAMA_BASE_URL=http://127.0.0.1:11434/v1` → 請求送到 **你自己電腦上的 Ollama**，不經過 OpenAI 官方、**不會因為這支程式被收費**。
- `OLLAMA_API_KEY` 可填任意字串（例如 `ollama`），本機 Ollama **不驗證**。

只有當你把 `OLLAMA_BASE_URL` 改成 OpenAI 或別家**雲端**網址並使用對方金鑰時，才會依該服務計費。

---

## 目錄長這樣（建議記法）

```
local_agent_demo/
├── README.md          ← 你現在看的：結構說明
├── requirements.txt   ← Python 依賴（openai SDK）
├── config.py          ← 本機 URL、模型名、最大步數（集中設定）
├── tools.py           ← 「手腳」：可被呼叫的函式 + TOOL_REGISTRY
└── agent.py           ← 「迴圈」：問 LLM → 解析 TOOL/FINAL → 執行工具
```

| 檔案 | 做什麼 |
|------|--------|
| **config.py** | 之後要換模型、換埠號，只改這裡（或用環境變數）。 |
| **tools.py** | 所有「真實動作」放這；**不要**讓 LLM 直接執行任意程式碼。 |
| **agent.py** | 只負責對話流程與呼叫 `run_tool`；商業邏輯盡量放在 tools。 |

---

## 為什麼這樣分？

- **改設定**不用翻整支 agent。
- **加能力** = 加函式 + 註冊 + 更新 `SYSTEM` 裡的工具說明。
- **除錯**時先看工具回傳字串，再看模型下一輪怎麼接。

---

## 怎麼跑

1. 先開 **Ollama**，並已 `ollama pull` 你的模型（預設名稱 `llama3.2`）。
2. 安裝依賴：

   ```powershell
   cd local_agent_demo
   pip install -r requirements.txt
   ```

3. 執行（不帶參數會用內建範例任務）：

   ```powershell
   python agent.py
   ```

   自訂問題：

   ```powershell
   python agent.py 請讀 README.md 並用兩句中文說明這個資料夾用途
   ```

4. 可選環境變數：`OLLAMA_BASE_URL`、`OLLAMA_MODEL`。

---

## 之後要擴充時

- **更多工具**：在 `tools.py` 加函式 → `TOOL_REGISTRY` → 改 `agent.py` 的 `SYSTEM`。
- **更正式**：可改成 OpenAI 相容的 `tools` / `tool_choice`（需模型支援 tool calling）。
- **正式專案**：可把 `local_agent_demo` 整包改名成 `my_agent`，或移進你的主專案當子套件。

---

## 安全提醒

`read_text_file` 已限制只能讀 **本資料夾內** 路徑。若之後加「下單、刪檔」等工具，務必再加權限與人工確認。
