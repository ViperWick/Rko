# AI 對話時資料從哪來（你不用自己翻檔）

你的使用方式可以是：

- **想自己看帳戶、點按鈕** → 用 **Streamlit**（`啟動檔/run_ui.bat`）。
- **想跟我討論、要我幫你查數字** → 在 **Cursor 對話**裡直接問，例如：「幫我看現在持倉」「現金比例多少」「前五大虧損標的」。

我會在專案裡用終端或讀檔幫你抓資料，你不必記檔案在哪。

---

## 我會用到的指令（在 repo 根目錄）

| 你想知道 | 典型做法 |
|----------|----------|
| 當下持倉／餘額／損益 | `py -m etoro_trading portfolio` |
| 寫入最新 JSON 再分析 | `py -m etoro_trading.scripts export-portfolio` |
| 今日組合與市場 | `py -m etoro_trading.scripts daily-performance` |

需已設定 **`etoro_trading/.env`**（API 金鑰）。

---

## 我會讀的檔案（快取／報表）

| 路徑 | 內容 |
|------|------|
| `etoro_trading/data/portfolio_summary.json` | 依標的彙總持倉（先跑 export-portfolio 較新） |
| `etoro_trading/data/daily_performance_report.json` | 每日績效腳本 |
| `etoro_trading/docs/策略討論_*.md` | 你在 UI 儲存的討論摘要，也可在 Cursor 用 @ 提到 |
| `etoro_trading/docs/今日總結_*.md` | 今日總結腳本產出 |

---

## 和「貼摘要」的關係

- 你仍可從 UI **產生策略討論摘要**後貼到對話，內容最完整（含各標的綜合評分）。
- 若懶得貼，**直接問我查**，我會用上面的指令／JSON 回答能算的部分。

詳細流程見：`如何用_Cursor_當策略討論_AI_agent.md`。
