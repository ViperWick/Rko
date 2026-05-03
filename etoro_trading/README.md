# eToro 交易程式

> **只想雙擊開程式？** → 打開資料夾 **[`啟動檔/`](啟動檔/README_啟動檔.md)**，照裡面的表選一個 `.bat` 即可。  
> **想跟我（Cursor AI）聊天、由我幫你查持倉／報表？** → 看 [`docs/AI對話時資料從哪來.md`](docs/AI對話時資料從哪來.md)；帳戶畫面仍用 Streamlit 即可。  
> **想專聊大盤／產業／個股邏輯（股市探討 Agent）？** → 見上層 [`.cursor/README_股市探討_Agent.md`](../.cursor/README_股市探討_Agent.md)。

**程式碼結構**（根目錄只留套件入口，其餘分資料夾）：

| 資料夾 | 內容 |
|--------|------|
| **`core/`** | API、持倉、交易、策略、風險、CLI `main.py` |
| **`signals/`** | 均線、RSI、波動等訊號模組 |
| **`ui/`** | Streamlit 介面、`ppt_images/`、產 PPT 腳本 |
| **`scripts/`** | 輔助匯出／報表（`py -m etoro_trading.scripts`） |
| **`啟動檔/`** | 所有 `.bat` 與啟動說明 |
| **`data/`** / **`docs/`** | 資料與文件 |

透過 eToro API 管理資產：查詢資產、自動下單、簡單策略、監控持倉。

## 功能

| 功能 | 說明 |
|------|------|
| **查詢資產** | 餘額、持倉、PnL、訂單 |
| **自動下單** | 買入、賣出、平倉 |
| **簡單策略** | 定額定投、止盈止損、60日均線過濾 |
| **監控持倉** | 定時檢查、自動止盈止損 |

## 安裝

```bash
cd etoro_trading
pip install -r requirements.txt
```

## 設定

1. 複製 `.env.example` 為 `.env`
2. 在 eToro 網站：**設定 > 交易 > API 金鑰管理** 建立金鑰
3. 將金鑰填入 `.env`：

```
ETORO_API_KEY=你的API金鑰
ETORO_USER_KEY=你的用戶金鑰
ETORO_MODE=demo
```

> ⚠️ **安全提醒**：若您曾在聊天中分享過 API 金鑰，請立即在 eToro 重新生成新金鑰並停用舊金鑰。  
> 
> **金鑰說明**：eToro 需要兩個金鑰（從 設定 > 交易 > API 金鑰管理 取得）：
> - `x-api-key`（Public API Key）
> - `x-user-key`（User Key）  
> 若 eToro 只提供一個金鑰，可將兩者設為相同值試試。若出現 `InvalidKey` 錯誤，請確認帳戶已驗證且金鑰權限包含 Read/Write。

## Web UI（圖形介面）

```bash
cd C:\Users\User\.cursor-tutor
streamlit run etoro_trading/ui/app_ui.py
```

或雙擊 **`啟動檔/run_ui.bat`**。啟動後在瀏覽器開啟 http://localhost:8501

### 簡易展示（給別人看、不需 API 金鑰）

若只想展示「介面長怎樣、有哪些功能」、不接真實帳戶，可執行：

```bash
streamlit run etoro_trading/ui/app_ui_demo.py
```

或雙擊 **`啟動檔/run_ui_demo.bat`**

會顯示：功能總覽、策略配置摘要、API 對照、介面截圖；無需設定 `.env` 或金鑰。

---

## CLI 使用方式

```bash
# 查詢資產
python -m etoro_trading portfolio

# 買入 100 美元 BTC
python -m etoro_trading buy BTC 100

# 賣空 50 美元 AAPL
python -m etoro_trading sell AAPL 50

# 平倉（填入持倉 ID）
python -m etoro_trading close 12345678

# 定額定投 50 美元 BTC
python -m etoro_trading dca BTC 50

# 60日均線過濾定投（價>MA60且偏離≥2%才買，否則跳過）
python -m etoro_trading dca-ma60 GLD 50

# 查詢 60日均線訊號（不下單，可用 yfinance）
python -m etoro_trading ma60-signal GLD

# 監控（止盈 20%、每標的保留 1/3、不設止損）
python -m etoro_trading monitor --take-profit 20 --keep-ratio 0.333 --no-stop-loss

# 監控（止盈 20% 全平、止損 -10%）
python -m etoro_trading monitor --stop-loss -10 --take-profit 20 --keep-ratio 0
```

### 輔助腳本

- **Windows**：雙擊 **`啟動檔/run_scripts_menu.bat`**（數字選功能；`0` 結束）。
- **終端機**（repo 根目錄）：`py -m etoro_trading.scripts --help`  
  例：`py -m etoro_trading.scripts export-portfolio`、`quantum-xlsx`  
  （舊寫法 `py -m etoro_trading.scripts.模組名` 仍可用。）

啟動方式總表：**一律看 `啟動檔/README_啟動檔.md`**。

## 模式

- `ETORO_MODE=demo`：模擬帳戶（建議先測試）
- `ETORO_MODE=real`：真實帳戶

## 免責聲明

本程式僅供學習與個人使用。投資有風險，請謹慎評估並自負盈虧。
