# AI Agent 完整架構與實作指南 PPT

## 📁 檔案位置

**PPT 檔案**：`AI_Agent_Guide.pptx`

可直接用 Microsoft PowerPoint、WPS、Google Slides 或 LibreOffice Impress 開啟。

---

## 📷 流程圖圖片

`images/` 資料夾內含 4 張流程圖：
- `agent_architecture.png` - 四層架構圖
- `tool_calling_flow.png` - 工具調用流程
- `integration_architecture.png` - 服務整合架構
- `react_loop.png` - ReAct 迴圈

---

## 📋 PPT 內容大綱（共 22 頁，含流程圖）

| 頁碼 | 標題 |
|------|------|
| 1 | 封面 |
| 2 | Part 1：什麼是 AI Agent？ |
| 3 | Agent 的定義 |
| 4 | Agent 調動的是什麼？ |
| 5 | **工具調用流程圖**（流程圖） |
| 6 | 常見工具類型 |
| 7 | Part 2：Agent 四層架構 |
| 8 | 四層核心架構 |
| 9 | **四層架構與 ReAct 迴圈流程圖**（流程圖） |
| 10 | AI 使用方式光譜 |
| 11 | Part 3：如何整合 Slack、GitHub、API？ |
| 12 | 基本原理：API + 授權 |
| 13 | 三種實作路線 |
| 14 | **服務整合架構圖**（流程圖） |
| 15 | 常見服務 API 支援 |
| 16 | Part 4：股票 API 與自動下單 |
| 17 | 技術上可行，但風險高 |
| 18 | 風險與注意事項 |
| 19 | Part 5：完整架構總覽 |
| 20 | Agent 可調動的服務架構 |
| 21 | **完整架構總覽圖**（流程圖） |
| 22 | 實作建議總覽 |
| 23 | 結尾 |

---

## 🔄 如何重新生成 PPT

若想修改內容後重新產生：

```powershell
cd C:\Users\User\.cursor-tutor\AI_Agent_PPT
pip install python-pptx
python generate_ai_agent_ppt.py
```

或使用 `py -3`：

```powershell
py -3 generate_ai_agent_ppt.py
```

---

## 📝 自訂內容

編輯 `generate_ai_agent_ppt.py` 可修改：
- 投影片標題與內容
- 新增/刪除投影片
- 調整章節結構
