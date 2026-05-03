# 量子／量子安全相關 — eToro 可搜尋代碼（子清單）

> **一頁總表**：請優先搭配 **`量子板塊_總覽與儀表板.md`**（分類 × eToro × 上市狀態一表看完）。  
> **用途**：本清單由專案內 `EToroClient.search_instrument(代碼)` **批次驗證**；僅代表「eToro 市場資料 API 能對應到該代碼」，**不代表** eToro 在你地區一定可買賣。  
> **投資決策由你自負**；本檔為輔助工具產出。  
> **驗證日期**：2026-03-21（部分代碼另於總表 M4 補驗 WIMI／UIS／ASPI 等）  

---

## 已驗證可搜尋（`internalSymbolFull`）

| 搜尋代碼 | eToro `internalSymbolFull` | `instrumentId` | 備註 |
|----------|----------------------------|----------------|------|
| IONQ | IONQ | 9425 | 純量子 |
| RGTI | RGTI | 10655 | 純量子 |
| QBTS | QBTS | 10881 | 純量子 |
| QUBT | QUBT | 14284 | 純量子 |
| ARQQ | ARQQ | 14435 | 後量子／加密敘事 |
| IBM | IBM | 1020 | 大廠量子 |
| GOOGL | GOOGL | 6434 | 大廠量子 |
| MSFT | MSFT | 1004 | 大廠量子 |
| AMZN | AMZN | 1005 | 大廠量子 |
| INTC | INTC | 1021 | 大廠量子 |
| HON | HON | 1469 | 與 Quantinuum 敘事相關 |
| SKYT | SKYT | 10289 | 代工／供應鏈 |
| LAES | LAES | 14375 | SEALSQ 相關代碼 |
| ASPI | ASPI | 14374 | 供應鏈／材料（題材需自行核實） |
| WIMI | WIMI | 13659 | 高風險名單常見標的 |
| UIS | UIS | 10737 | 高風險名單常見標的 |

---

## 本次驗證「搜尋不到」（可能未上架或代碼不同）

| 你輸入的代碼 | 說明 |
|--------------|------|
| INFQ | 可改試 App 內完整名稱搜尋「Infleqtion」或上市後 eToro 是否補上架 |
| XNDU | 新上市／雙掛牌，eToro 可能延後或不同代碼 |
| QNC | TSXV，eToro 常未涵蓋小板 |
| BTQ | NEO 板，可能未上架 |
| ONE | TSX `01 Communique`，可試 `ONE` 以外寫法或僅用名稱搜尋 |
| AMPG | API 回傳無 instrument（或尚未支援） |
| ZENA | 同上 |
| FCCN | OTC，多數情況未上架 |

**建議**：在 eToro App 手動搜公司全名，若找到新代碼，請補進本表並註明日期。

---

## 如何重新驗證（本機）

在 repo 根目錄、已設定 `etoro_trading/.env` 時：

```bash
cd C:\Users\User\.cursor-tutor
py -c "from etoro_trading.core.etoro_client import EToroClient; c=EToroClient(); print(c.search_instrument('IONQ'))"
```

或擴充 `symbols = [...]` 批次迴圈（與主清單維護者同步即可）。
