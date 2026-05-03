# eToro Agent Portfolio API 探索備忘錄

- 建立日期：2026-04-17
- 用途：明日續聊 — 把今天和 AI 討論出的 Agent Portfolio 機制、整合路徑、下一步決策留存
- 接續方式：在 Cursor 對話用 `@etoro_trading/docs/2026-04-17_AgentPortfolio探索備忘.md` 提及本檔

---

## 一、今天的觸發點

- 在 eToro 介面看到**推出代理人投資組合 (Agent Portfolio)** 的新功能宣傳卡片。
- 宣傳重點：「為你打造的代理投資組合」、「選擇管理人」、「你的配置你掌控」、「使用風險須自行承擔」。
- 核心問題：**「可以跟 AI 探討出一個自動交易程式，並利用這個 API 直接進行操作嗎？」**
- 答案：**可以**，且 eToro 已經開放完整官方 API（`/api/v1/agent-portfolios`）。

---

## 二、Agent Portfolio 運作機制（查文件後確認）

這不是「單純子帳戶」，是**「AI 版 CopyTrader」＋ 風險隔離的 API 沙盒**。

```
你主帳戶 (Main Account)
   │
   ├── 拿出 investmentAmountInUsd (例 $2,000) 複製 →
   │
   └── Agent Portfolio（虛擬帳戶 agentPortfolioVirtualBalance 例 $10,000）
          ↑
          │ 用受限 User Token 下單
          │
       AI Agent 程式（可以是你的 etoro_trading）
```

**關鍵四點：**

1. `agentPortfolioVirtualBalance` 是虛擬分母（標準化績效比較用）。
2. `investmentAmountInUsd` = 從你主帳戶**實際扣**的金額，決定鏡射比例。
3. Agent 每開一個倉，按比例鏡射到主帳戶（例：Agent 開 $3k，你實扣 $600 = 20%）。
4. **你主帳戶最大曝險 = `investmentAmountInUsd`**，程式再怎麼亂搞也超不過這個數字。

### Token 權限 Scopes

| scopeId | 權限 |
|---|---|
| 200 | etoro-public:real:read |
| 201 | etoro-public:demo:read |
| 202 | etoro-public:real:write ← 可下真單 |
| 203 | etoro-public:demo:write ← 建議先用這個 |

Token 另外支援：
- `ipsWhitelist` — 限定來源 IP
- `expiresAt` — 自動過期
- 可隨時 `delete` 撤銷

---

## 三、API 圖譜

```
POST   /api/v1/agent-portfolios                              # 創建 Portfolio（+ token）
GET    /api/v1/agent-portfolios                              # 列出所有 Agent Portfolios
DELETE /api/v1/agent-portfolios/{id}                         # 停止鏡射 + 刪除
POST   /api/v1/agent-portfolios/{id}/user-tokens             # 新增 token
DELETE /api/v1/agent-portfolios/{id}/user-tokens/{tokenId}   # 撤銷 token
```

### 創建 Payload 範例

```json
{
  "investmentAmountInUsd": 500,
  "agentPortfolioName": "DCARsi",
  "agentPortfolioDescription": "DCA + RSI 測試策略",
  "userTokenName": "bot-dca-rsi",
  "scopeIds": [203],
  "expiresAt": "2026-07-31T23:59:59Z"
}
```

### 認證

沿用既有的 `x-api-key` + `x-user-key` + `x-request-id` 三 headers（和 `etoro_trading/core/etoro_client.py` **完全相容**）。

### Rate Limits

- 讀取 60 req/min
- 下單 / 寫入 20 req/min
- 超過 → 429 Too Many Requests（需 exponential backoff）

---

## 四、對現有 `etoro_trading/` 專案的意義

### 已具備（無需重寫）

- ✅ `core/etoro_client.py` — 認證 + 下單 + 平倉 + 查倉
- ✅ `core/trading.py` — `buy` / `sell` / `close`
- ✅ `signals/` — RSI、MA、突破、散戶、波動訊號
- ✅ `core/composite_score.py` — 綜合評分
- ✅ `core/strategy.py` — 策略框架
- ✅ `core/risk_score.py` / `core/monitor.py` — 風險模組
- ✅ `scripts/run_daily_automation.ps1` — 日排程

### 升級成「自動交易 Agent」還缺的四件

1. **決策閉環**：從「訊號 → 倉位目標 → 實際下單」一支主程式（暫名 `auto_trader.py`）。
2. **硬性風控層**：單筆最大部位 %、單日最大虧損 kill switch、板塊集中度上限。
3. **狀態機 / 去重**：避免同一訊號當天下多次單。
4. **日誌 + 審計**：每筆決策寫 JSON 供事後 review。

---

## 五、可以玩的架構（多策略平行實驗）

```
etoro_trading/
  agents/
    dca_rsi/
      .env              # 自己的 agentPortfolioId + token
      config.yml
    breakout/
      .env
      config.yml
    quantum_rotation/
      .env
      config.yml
  core/
    agent_portfolio.py  # 新增：管理 Agent Portfolio 的模組
    auto_trader.py      # 新增：決策閉環主程式
```

三個月後比較績效 → 贏家加碼、輸家 `delete-agent-portfolio` 立即止血。

---

## 六、三條紅線（認真遵守）

1. **滿倉 −23% 的主帳戶不是實驗場**。先處理滿倉現金 0.8% 的問題，再談自動化。
2. **Phase 0 一律 demo (scope 203)**。跑通全迴圈 + 人工審 log 至少 1~2 週才考慮 real。
3. **真錢實驗**入金 $500 ~ $1,000 到一個 Agent Portfolio，**絕不動主帳戶**。

---

## 七、現況快照（作為明日續聊的起點）

來源：`etoro_trading/data/portfolio_summary.json`（最近一次快照）

| 項目 | 數值 |
|---|---|
| 總權益 | $88,353 |
| 未實現 PnL | −$26,731（≈ −23%） |
| 現金比例 | 0.8% |
| 持倉數 | 1,841 筆 |

**大幅虧損集中**：ETH、ADA、NKE、PLUG、CRM、BBBY、TDOC、PYPL  
**少數亮點**：OCGN +117%、TRX +10.3%、PLTR +10.2%、DDD +7.3%、GEVO +0.3%

---

## 八、明日可選的下一步（挑一個開工）

1. **查費率細節** — 挖 eToro 對 Agent Portfolio 的點差、管理費、抽成規則（文件目前沒提，需要看平台條款或實測）。
2. **寫 `agent_portfolio.py` 模組** — 在 `etoro_trading/core/` 新增 Create / List / Delete / Token 管理，demo 模式可跑。
3. **設計 multi-agent 架構** — 規劃 `agents/` 資料夾結構與多 `.env` 設定。
4. **Demo POC** — 寫 `py -m etoro_trading.scripts create_agent_portfolio --demo`，打通整套流程。
5. **先處理主帳戶滿倉問題** — 止盈 OCGN、評估結構性套牢部位，把現金比率拉回 5~10%，再談 Agent Portfolio。

**建議順序：5 → 1 → 4 → 2 → 3**  
（先救主帳戶 → 搞清費用 → 用 demo 驗證 API → 寫模組 → 擴展多策略）

---

## 九、備用資料連結

- eToro API 文件：`https://api-portal.etoro.com/`
- Agent Portfolio 區：`/api-reference/agent-portfolios/`
- Cursor MCP 已裝好：`user-etoro-api-docs`（可用 `search_e_toro_api_docs` / `query_docs_filesystem_e_toro_api_docs` 再查）
- 官方 AI Skill：`https://skills.bullaware.com/etoro-api/SKILL.md`
