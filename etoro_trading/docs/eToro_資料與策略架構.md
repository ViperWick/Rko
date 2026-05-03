# eToro 可取得資料與自動交易策略架構

## 一、我們能從 eToro 取得什麼資訊？

### 1. 市場數據 (Market Data)

| API | 用途 | 策略相關性 |
|-----|------|------------|
| **即時報價** `GET /instruments/rates` | 買賣價、最新成交價、轉換匯率 | ⭐⭐⭐ 下單前確認價格 |
| **歷史 K 線** `GET /instruments/{id}/history/candles/{direction}/{interval}/{count}` | OHLCV（開高低收量） | ⭐⭐⭐ 策略回測、技術指標 |
| **搜尋標的** `GET /market-data/search` | 代碼→Instrument ID、currentRate 等 | ⭐⭐⭐ 必備 |
| **歷史收盤價** | 全標的收盤價 | ⭐⭐ 大範圍分析 |
| **標的類型** | 股票、ETF、加密、商品等分類 | ⭐ 篩選標的 |

**K 線週期**：1 分鐘、5 分、10 分、15 分、30 分、1 小時、4 小時、1 日、1 週  
**K 線上限**：單次最多 1000 根

---

### 2. 帳戶與持倉 (Trading Info)

| API | 用途 | 策略相關性 |
|-----|------|------------|
| **投資組合 PnL** `GET /trading/info/{demo\|real}/pnl` | 餘額、持倉、訂單、未實現損益 | ⭐⭐⭐ 風控、倉位管理 |
| **訂單詳情** | 單筆訂單與對應持倉 | ⭐⭐ 追蹤成交 |
| **交易歷史** (Real) | 歷史成交紀錄 | ⭐⭐ 績效分析 |

**持倉欄位**：positionId、instrumentId、amount、units、openRate、pnL、isBuy、leverage、stopLossRate、takeProfitRate

---

### 3. 其他（策略可選）

| API | 用途 |
|-----|------|
| Watchlist | 自訂監控清單 |
| 市場推薦 | 平台推薦標的 |
| 跟單者資訊 | 跟單數據 |
| WebSocket | 即時串流報價 |

---

## 二、模擬交易 vs 實盤流程

```
┌─────────────────────────────────────────────────────────────────┐
│  第一階段：本地模擬（不連 eToro）                                  │
├─────────────────────────────────────────────────────────────────┤
│  1. 從 eToro 下載歷史 K 線 → 存成 CSV/DB                          │
│  2. 用歷史資料跑策略邏輯 → 產生「模擬買賣訊號」                     │
│  3. 虛擬帳戶：模擬餘額、持倉、損益                                 │
│  4. 回測績效：勝率、最大回撤、夏普比等                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 驗證通過
┌─────────────────────────────────────────────────────────────────┐
│  第二階段：eToro 實盤（連線 API）                                  │
├─────────────────────────────────────────────────────────────────┤
│  1. 用同一套策略邏輯，但資料改為：                                 │
│     - 即時報價 (rates) 或 WebSocket                              │
│     - 真實持倉 (portfolio)                                        │
│  2. 訊號產生後 → 呼叫 eToro 下單 API                               │
│  3. 真實餘額、持倉、損益                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、策略模擬程式架構建議

```
etoro_trading/
├── etoro_client.py      # 現有：eToro API
├── data/                # 新增：歷史資料
│   ├── fetcher.py       # 從 eToro 拉 K 線
│   └── candles/        # 存 CSV（BTC_1h.csv 等）
├── simulator/           # 新增：模擬引擎
│   ├── account.py       # 虛擬帳戶（餘額、持倉）
│   ├── engine.py        # 回測迴圈：逐 K 線跑策略
│   └── metrics.py      # 績效計算
├── strategies/          # 新增：策略邏輯
│   ├── base.py         # 策略介面
│   └── ma_cross.py     # 例：均線交叉
└── live/                # 新增：實盤（用同一策略）
    └── runner.py       # 定時跑策略 + 呼叫 eToro 下單
```

---

## 四、策略介面設計（模擬與實盤共用）

```python
class Strategy:
    def on_bar(self, symbol: str, bar: dict, account) -> list[Signal]:
        """每根 K 線觸發，回傳買賣訊號"""
        # bar = {open, high, low, close, volume, time}
        pass

    def on_position_update(self, position, account):
        """持倉更新時（可選）"""
        pass
```

---

## 五、下一步

1. **建立資料 fetcher**：從 eToro 拉 K 線並存檔  
2. **建立模擬引擎**：用歷史 K 線跑策略、計算虛擬損益  
3. **實作範例策略**：如均線交叉、RSI  
4. **驗證通過後**：建立 live runner，連 eToro 實盤下單  
