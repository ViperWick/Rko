# eToro Alpha Portfolios 定期追蹤

## 限制說明

eToro **不提供** Smart Portfolio 持倉的公開 API，無法自動取得 PureMomentum、Momentum-LS、PureGrowth、MarketPicks 等組合的成分股。

因此採用**手動輸入 + 定期追蹤**方式。

---

## 使用流程

### 1. 取得成分股

登入 eToro → **投資組合** → 選擇目標組合（如 Momentum-LS）→ **基本情況** 或 **持倉** 分頁 → 複製股票代碼列表。

### 2. 填入設定檔

編輯 `etoro_trading/data/alpha_portfolios.json`，在對應組合的 `symbols` 陣列填入代碼，例如：

```json
{
  "id": "momentum-ls",
  "name": "Momentum-LS",
  "symbols": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", ...]
}
```

### 3. 執行追蹤

```bash
python -m etoro_trading.scripts.track_alpha_portfolios
```

會產生：
- `alpha_portfolios_tracking.json`：完整結果
- `alpha_portfolios_tracking.csv`：可匯入試算表

### 4. 定期執行（選做）

- **Windows 工作排程**：每週一執行
- **手動**：每月再平衡後更新一次 `alpha_portfolios.json` 並執行腳本

---

## 追蹤內容

| 項目 | 說明 |
|------|------|
| 近 20 日報酬 | 等權重模擬（yfinance 價格） |
| 成分股數 | 有填入的標的數量 |

**注意**：此為**模擬報酬**，非 eToro 官方績效。eToro 組合有權重、再平衡、做空等，實際報酬可能不同。

---

## 四個投資組合對應

| 圖示名稱 | eToro 頁面 | 類型 |
|----------|------------|------|
| PureMomentum | 投資組合搜尋 | 方向性 |
| Momentum-LS | smartportfolios/momentum-ls | 方向性 |
| PureGrowth | 投資組合搜尋 | 專業 |
| MarketPicks | 投資組合搜尋 | 專業 |

若找不到對應頁面，可在 eToro 投資組合列表搜尋名稱。
