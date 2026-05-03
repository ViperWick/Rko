# Ollama 本機摘要（自動化 log）

用 **本機 Ollama** 讀 `data/automation_logs/daily_*.log`，產生一段**繁中摘要**（成功／失敗／留意一句），寫入同目錄 `ollama_summary_*.md`。

---

## 1. 安裝 Ollama

1. 下載安裝：<https://ollama.com>（Windows 有安裝程式）。
2. 終端機執行（擇一模型，名稱需與下方 `OLLAMA_MODEL` 一致）：

```bash
ollama pull llama3.2
```

其他常用：`qwen2.5:7b`、`mistral`、`gemma2:2b`（較小、較快）。

3. 確認服務在跑：瀏覽器開 `http://127.0.0.1:11434` 或執行 `ollama list`。

---

## 2. 專案設定（可選）

在 **`etoro_trading/.env`** 可加：

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=llama3.2
```

---

## 3. 執行摘要

在 **repo 根目錄**：

```bash
py -m etoro_trading.scripts ollama-summarize
```

### 3.1 一鍵執行（不用打指令）

- **集中入口**：雙擊 **`ai_agents/啟動_eToro_Ollama摘要一鍵.bat`** 或 **`ai_agents/選單_啟動AI_Agent.bat`** 選 2。  
- 或雙擊 **`etoro_trading/啟動檔/一鍵_Ollama摘要.bat`**（同上指令，效果等同選單選 20）。

進階：在該 `.bat` 上按右鍵 → 建立捷徑 → 捷徑右鍵「內容」→「快速鍵」可設 **Ctrl+Alt+某鍵**，之後按快捷鍵即跑。

### 3.2 講一句話就跑（語音）

1. 安裝語音依賴（只需一次）：

```bash
pip install -r etoro_trading/requirements-voice.txt
```

若 **PyAudio** 安裝失敗，請看 `requirements-voice.txt` 內的 `pipwin` 說明。

2. 先開 **Ollama**，再擇一：

- **雙擊** `ai_agents/啟動_eToro_語音摘要監聽.bat` 或 `etoro_trading/啟動檔/啟動_語音摘要監聽.bat`（不必開 Cursor、不必手打指令），或  
- 在 repo 根目錄執行：

```bash
py -m etoro_trading.scripts listen-ollama-summarize
```

3. 對麥克風說例如：**「執行摘要」**、**「開始摘要」**、**「跑摘要」**（須符合腳本內關鍵字規則）。

說明：預設使用 **Google 線上語音辨識（zh-TW）**，需要網路；按 **Ctrl+C** 結束監聽。

指定某個 log：

```bash
py -m etoro_trading.scripts ollama-summarize --log etoro_trading/data/automation_logs/daily_20260321_120000.log
```

指定模型與 URL：

```bash
py -m etoro_trading.scripts ollama-summarize --ollama-model qwen2.5:7b --ollama-base-url http://127.0.0.1:11434/v1
```

---

## 4. 接在日常排程後面（可選）

編輯 **`etoro_trading/scripts/run_daily_automation.ps1`**，在 `$Steps` 陣列**最後**加一行：

```powershell
    @{ Name = "ollama-summarize"; Args = @("-m", "etoro_trading.scripts", "ollama-summarize") }
```

若 Ollama 沒開，該步會失敗；可加上 `-StopOnError:$false` 預設行為（目前已預設失敗仍繼續），或維持不加此步、改**手動**跑摘要。

---

## 5. 免責

摘要僅供快速瀏覽排程結果，**非投資建議**。投資決策請自行判斷。
