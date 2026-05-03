# eToro API 金鑰管理規範

> 建立日期：2026-04-18  
> 目的：集中管理 eToro 主帳戶 key 與各 Agent Portfolio 的 userToken，避免秘文外洩與版本混亂。  
> 配套檔案：`.env.example`、`agents/_template/.env.example`、`.gitignore`

---

## 一、鐵律（任何情境都不能破）

1. **Token 秘文只回傳一次**  
   `POST /api/v1/agent-portfolios`（或 `/user-tokens`）回來的 `userToken` 欄位，離開 response 就再也調不回來。沒寫進 `.env` 就得刪掉重發。

2. **秘文絕不進三個地方**  
   - ❌ Git（含 commit、PR、tag、注釋）
   - ❌ AI 對話（含本檔案、Cursor chat、截圖）
   - ❌ 本機日誌 / 終端機輸出（`print` 禁列印 token 內容）

3. **本檔案只記 metadata，不記秘文**  
   允許寫：portfolio 名稱、portfolio ID、token ID、client ID、scope、到期日、建立時間、IP 白名單、用途描述。  
   禁止寫：`userToken`（`sk_live_...`）、`x-user-key` 內容、`x-api-key` 內容。

4. **外洩應變**  
   一旦懷疑秘文出現在不該出現的地方，**立刻**用主帳戶 key 打：
   - 單把撤銷：`DELETE /api/v1/agent-portfolios/{portfolioId}/user-tokens/{tokenId}`
   - 整個 portfolio 撤：`DELETE /api/v1/agent-portfolios/{portfolioId}`  
   撤完再重發新 token，並在本檔案「輪替紀錄」補一條。

5. **Phase 0 一律 demo（scope 203）**  
   在人工審 log 至少 1~2 週、確認策略行為正常前，所有 Agent 的 scope 只給 `[203]`。

---

## 二、金鑰種類與放置位置

| 名稱 | 性質 | 放置位置 | 誰會讀 |
|---|---|---|---|
| `ETORO_API_KEY`（Public API Key） | 應用識別 | `etoro_trading/.env` | 所有主帳戶腳本、Agent 管理腳本 |
| `ETORO_USER_KEY`（主帳戶 User Key） | 主帳戶身分 | `etoro_trading/.env` | 只有 Agent 管理腳本（建立/刪除 Portfolio） |
| `AGENT_USER_TOKEN`（Agent 的 userToken） | Agent 沙盒身分 | `etoro_trading/agents/<策略>/.env` | 只有該 Agent 的策略程式 |
| `AGENT_PORTFOLIO_ID` | 非秘文 metadata | `etoro_trading/agents/<策略>/.env` + 本檔案清單 | 策略程式 + 人讀 |
| `AGENT_USER_TOKEN_ID` | 非秘文 metadata | `etoro_trading/agents/<策略>/.env` + 本檔案清單 | 撤銷 token 時用 |

### 資料夾規劃

```
etoro_trading/
├── .env                          # 主帳戶 key（gitignored）
├── .env.example                  # 主帳戶範本（可提交）
├── agents/
│   ├── _template/
│   │   └── .env.example          # 每個新 Agent 複製用的範本
│   ├── dca_rsi/
│   │   ├── .env                  # 此 Agent 專屬 token（gitignored）
│   │   └── config.yml            # 策略參數（可提交）
│   └── breakout/
│       ├── .env
│       └── config.yml
└── docs/
    └── API金鑰管理.md             # 本檔案
```

### `.gitignore` 規則

```
.env
agents/**/.env
```

---

## 三、Scope 權限表

| scopeId | 名稱 | 意義 | 使用時機 |
|---|---|---|---|
| 200 | `etoro-public:real:read` | 讀真實帳戶 | 監控腳本 |
| 201 | `etoro-public:demo:read` | 讀 demo 帳戶 | Demo 監控 |
| 202 | `etoro-public:real:write` | 真實下單 | **人工審過才可開啟** |
| 203 | `etoro-public:demo:write` | Demo 下單 | Phase 0 一律用這個 |

---

## 四、Agent Portfolio 清單

> 每建立一個新的 Agent Portfolio，就在此表新增一列。  
> 每次 token 輪替或刪除 portfolio，在「輪替紀錄」區段補一條。

### 4.1 現有 Agent Portfolio

| # | 名稱 (6-10 字元) | `agentPortfolioId` | `mirrorId` | 虛擬餘額 | 實扣金額 | 用途 | 建立日期 | 狀態 |
|---|---|---|---|---|---|---|---|---|
| — | *（尚未建立任何 Portfolio）* | | | | | | | |

### 4.2 現有 User Token

| # | 所屬 Portfolio | `userTokenName` | `userTokenId` | `clientId` | Scopes | IP 白名單 | 建立日期 | 到期日 | 狀態 |
|---|---|---|---|---|---|---|---|---|---|
| — | *（尚未建立任何 Token）* | | | | | | | | |

### 4.3 輪替 / 撤銷紀錄

| 日期 | 動作 | 對象 | 原因 | 操作人 |
|---|---|---|---|---|
| — | — | — | — | — |

---

## 五、標準操作 SOP

### SOP-1：建立新 Agent Portfolio（demo）

1. **命名**：想一個 6~10 字元、有辨識度的 `agentPortfolioName`（例：`DCARsi01`）。
2. **跑建立腳本**（待 `core/agent_portfolio.py` 寫好後會有 CLI）：
   ```bash
   py -m etoro_trading.scripts create-agent-portfolio \
       --name DCARsi01 \
       --desc "DCA + RSI 測試" \
       --invest 500 \
       --token-name bot-dca-rsi \
       --scopes 203 \
       --expires 2026-07-31
   ```
3. **立即處理 response**：
   - 把 `userToken` 秘文**只貼進** `agents/dca_rsi/.env`，內容如下：
     ```
     AGENT_USER_TOKEN=sk_live_xxxxxxxxxxxx
     AGENT_PORTFOLIO_ID=a1b2c3d4-...
     AGENT_USER_TOKEN_ID=f9e8d7c6-...
     AGENT_MIRROR_ID=12345
     ```
   - 把 metadata（不含秘文）寫進 §4.1 / §4.2 表格。
4. **驗證**：用此 token 打 `GET /api/v1/user/portfolio/demo`（或等同端點），確認能正常讀到 demo 帳戶。
5. **永遠不要** 把 response 原文貼進 chat、log、issue。

### SOP-2：輪替 Token（定期或外洩疑慮）

1. 先發新 token：`POST /api/v1/agent-portfolios/{id}/user-tokens`
2. 更新 `agents/<策略>/.env` 為新 token
3. 重啟該 Agent 程式，確認新 token 可用
4. 撤銷舊 token：`DELETE /api/v1/agent-portfolios/{id}/user-tokens/{oldTokenId}`
5. 在 §4.3 補一條紀錄

### SOP-3：從 Demo 升 Real

**此流程僅在以下條件全部成立時才執行：**
- [ ] 該 Agent demo 連續跑 ≥ 14 天
- [ ] 人工逐日審過決策 log
- [ ] 回測 + Demo 實盤淨值曲線合理
- [ ] 主帳戶滿倉 −23% 問題已解決，現金 ≥ 5%
- [ ] 該 Agent 單獨入金 $500~$1,000 的決定有寫下理由

**步驟**：
1. 撤銷該 Agent 的 scope 203 token
2. 新發一把 scope 202 token（附 IP 白名單 + 短期 `expiresAt`）
3. 更新 `.env` + 本文件 §4.2
4. 先手動單日觀察，確認無異常才讓程式自動跑
5. 在 §4.3 標註 "Demo → Real promotion"

### SOP-4：緊急熔斷（Kill Switch）

> 場景：Agent 行為異常、連續下單、帳戶異常變動。

1. **第一優先**：用主帳戶 key 打
   ```
   DELETE /api/v1/agent-portfolios/{id}
   ```
   → 整個 Portfolio（含所有 token、鏡射關係）一刀切斷。
2. 檢查主帳戶當下曝險：`GET /api/v1/user/portfolio/real`
3. 必要時手動平主帳戶被鏡射產生的異常倉位
4. 在 §4.3 紀錄事件，且事後 review log 找原因
5. 問題解決前**禁止**重建該策略的 Portfolio

---

## 六、本機 `.env` 實際寫法

### 主帳戶（`etoro_trading/.env`）

```ini
# 主帳戶 Key：從 eToro 設定 > 交易 > API 金鑰管理 取得
ETORO_API_KEY=<你的 Public API Key>
ETORO_USER_KEY=<你的主帳戶 User Key>

# 預設模式
ETORO_MODE=demo
```

### Agent（`etoro_trading/agents/<策略>/.env`）

```ini
# 由 POST /api/v1/agent-portfolios 建立時回傳，寫入後立刻驗證
AGENT_PORTFOLIO_ID=<agentPortfolioId>
AGENT_USER_TOKEN_ID=<userTokenId>
AGENT_USER_TOKEN=<userToken 秘文，只在建立當下出現一次>
AGENT_MIRROR_ID=<mirrorId>

# 策略識別
AGENT_NAME=DCARsi01
AGENT_SCOPE=203
```

策略程式載入時必須指定路徑，避免與主帳戶 `.env` 衝突：

```python
from dotenv import load_dotenv
load_dotenv("agents/dca_rsi/.env", override=True)
```

---

## 七、檢查清單（新建 Agent 前逐項打勾）

- [ ] `agentPortfolioName` 是 6~10 字元
- [ ] 已決定 `investmentAmountInUsd`（phase 0 建議 ≤ $500）
- [ ] Scope 只含 203（非 202）
- [ ] `expiresAt` 有設，且不超過 3 個月後
- [ ] `ipsWhitelist` 有設（即使是家用動態 IP 也先放個當時的 IP，不設等於裸奔）
- [ ] `agents/<策略>/` 資料夾已建好
- [ ] `.env` 已就位且 `.gitignore` 能擋到
- [ ] 建立成功後立即在本文件 §4.1 / §4.2 登記 metadata
- [ ] 沒有任何人看過 token 秘文（含你自己的截圖）

---

## 八、參考

- eToro API 文件入口：`https://api-portal.etoro.com/`
- Agent Portfolio 相關端點：`/api-reference/agent-portfolios/`
- 建立/機制備忘：`docs/2026-04-17_AgentPortfolio探索備忘.md`
- Cursor MCP：`user-etoro-api-docs`（`search_e_toro_api_docs` / `query_docs_filesystem_e_toro_api_docs`）
