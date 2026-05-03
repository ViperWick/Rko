# -*- coding: utf-8 -*-
"""
Agent Portfolio 金鑰驗證腳本

用途：
  1. 用主帳戶 key 打 GET /api/v1/agent-portfolios，列出所有 Agent Portfolio
     → 驗證主帳戶能看到 "the_future_world"
     → 取回 agentPortfolioId / mirrorId / userTokenId 等非秘文 metadata
  2. 用 Agent 的 key 打 GET /api/v1/trading/info/demo/pnl
     → 驗證 Agent 專屬的公鑰/私鑰能讀到自己的 demo 帳戶

安全：
  - 任何 token 秘文只遮罩顯示（前 4 + 後 4 字元）
  - 不下任何單、不修改任何資料
  - 讀取失敗時只印 status code + 前 300 字訊息

用法：
    py -m etoro_trading.scripts.verify_agent_portfolio
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import requests

# Windows 終端機預設 cp950，這裡強制 UTF-8 輸出避免中文 / 特殊符號崩潰
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_URL = "https://public-api.etoro.com"
AGENT_NAME = "the_future_world"


def _mask(value: str | None, show: int = 4) -> str:
    if not value:
        return "<空>"
    s = str(value)
    if len(s) <= show * 2:
        return "*" * len(s)
    return f"{s[:show]}...{s[-show:]}  (長度 {len(s)})"


def _parse_env_file(path: Path) -> dict[str, str]:
    """手動解析 .env（避免污染 os.environ 和主帳戶 key 混到）"""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip().strip('"').strip("'")
        # 忽略還沒填的 <佔位字元>
        if v.startswith("<") and v.endswith(">"):
            continue
        out[k.strip()] = v
    return out


def _headers(api_key: str, user_key: str) -> dict:
    return {
        "x-api-key": api_key,
        "x-user-key": user_key,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


def _get_repo_root() -> Path:
    # scripts/verify_agent_portfolio.py → repo root 是上兩層
    return Path(__file__).resolve().parent.parent


def test_main_list_agent_portfolios() -> list[dict]:
    """Test 1：用主帳戶 key 列出所有 Agent Portfolio"""
    print("\n" + "=" * 64)
    print("[Test 1] 用主帳戶 key 列出所有 Agent Portfolio")
    print("=" * 64)

    repo_root = _get_repo_root()
    main_env = _parse_env_file(repo_root / ".env")

    api_key = main_env.get("ETORO_API_KEY")
    user_key = main_env.get("ETORO_USER_KEY")

    if not api_key or not user_key:
        print(f"[FAIL] 主 .env 檔缺 ETORO_API_KEY 或 ETORO_USER_KEY：{repo_root / '.env'}")
        return []

    print(f"  x-api-key:  {_mask(api_key)}")
    print(f"  x-user-key: {_mask(user_key)}")

    url = f"{BASE_URL}/api/v1/agent-portfolios"
    try:
        resp = requests.get(url, headers=_headers(api_key, user_key), timeout=15)
    except requests.RequestException as e:
        print(f"✗ 網路錯誤：{e}")
        return []

    if resp.status_code != 200:
        print(f"[FAIL] HTTP {resp.status_code}：{resp.text[:300]}")
        return []

    data = resp.json()
    portfolios = data.get("agentPortfolios", [])
    print(f"\n[OK] 主帳戶名下共有 {len(portfolios)} 個 Agent Portfolio：\n")

    for p in portfolios:
        print(f"  --- {p.get('agentPortfolioName')} ---")
        print(f"      agentPortfolioId : {p.get('agentPortfolioId')}")
        print(f"      mirrorId         : {p.get('mirrorId')}")
        print(f"      virtualBalance   : ${p.get('agentPortfolioVirtualBalance')}")
        print(f"      createdAt        : {p.get('createdAt')}")
        tokens = p.get("userTokens", []) or []
        for t in tokens:
            print(f"      token: {t.get('userTokenName')}")
            print(f"        userTokenId  : {t.get('userTokenId')}")
            print(f"        scopeIds     : {t.get('scopeIds')}")
            print(f"        expiresAt    : {t.get('expiresAt')}")
            print(f"        ipsWhitelist : {t.get('ipsWhitelist')}")
        print()

    return portfolios


def test_agent_read_portfolio() -> bool:
    """Test 2：用 Agent 專屬 key 讀自己的 demo 帳戶"""
    print("\n" + "=" * 64)
    print(f"[Test 2] 用 Agent '{AGENT_NAME}' 的 key 讀自己 demo 帳戶")
    print("=" * 64)

    repo_root = _get_repo_root()
    agent_env_path = repo_root / "agents" / AGENT_NAME / ".env"
    agent_env = _parse_env_file(agent_env_path)

    api_key = agent_env.get("AGENT_API_KEY")
    user_token = agent_env.get("AGENT_USER_TOKEN")

    if not api_key or not user_token:
        print(f"[FAIL] Agent .env 裡 AGENT_API_KEY 或 AGENT_USER_TOKEN 還沒填好：{agent_env_path}")
        return False

    print(f"  x-api-key:  {_mask(api_key)}")
    print(f"  x-user-key: {_mask(user_token)}")

    url = f"{BASE_URL}/api/v1/trading/info/demo/pnl"
    try:
        resp = requests.get(url, headers=_headers(api_key, user_token), timeout=15)
    except requests.RequestException as e:
        print(f"[FAIL] 網路錯誤：{e}")
        return False

    if resp.status_code != 200:
        print(f"[FAIL] HTTP {resp.status_code}：{resp.text[:300]}")
        print("\n  可能原因：")
        print("    - key 貼錯（多餘空白/換行）")
        print("    - scope 不含讀權限（203 只有 demo write？需確認）")
        print("    - Agent Portfolio 只能用特定端點，不能打一般 trading/info")
        return False

    data = resp.json()
    equity = data.get("Equity") or data.get("equity") or data.get("TotalEquity")
    cash = data.get("Credit") or data.get("credit") or data.get("cash") or data.get("AvailableCash")
    positions = data.get("Positions") or data.get("positions") or []

    print(f"\n[OK] Demo 帳戶讀取成功")
    print(f"  Equity      : {equity}")
    print(f"  Cash/Credit : {cash}")
    print(f"  持倉數      : {len(positions)}")
    return True


def suggest_metadata_to_fill(portfolios: list[dict]) -> None:
    """從 Test 1 結果挑出 the_future_world，提示要補哪些欄位到 .env"""
    print("\n" + "=" * 64)
    print(f"建議補進 agents/{AGENT_NAME}/.env 的 metadata（非秘文）")
    print("=" * 64)

    if not portfolios:
        print("  （Test 1 沒成功，跳過）")
        return

    def _normalize(name: str) -> str:
        return (name or "").lower().replace(" ", "").replace("_", "")

    target_keys = ["thefutureworld", "futureworld", "tfworld", "futworld"]
    target = next(
        (p for p in portfolios if any(k in _normalize(p.get("agentPortfolioName", "")) for k in target_keys)),
        None,
    )
    if target is None and len(portfolios) == 1:
        target = portfolios[0]
        print(f"  （只有一個 Agent Portfolio，假定它就是 the_future_world）")

    if target is None:
        print("  找不到名稱相符的 Agent Portfolio。以下是全部清單，請自行對照：")
        for p in portfolios:
            print(f"    - {p.get('agentPortfolioName')} → {p.get('agentPortfolioId')}")
        return

    tokens = target.get("userTokens", []) or []
    token_id = tokens[0].get("userTokenId") if tokens else ""

    print(f"\n  # 請把這幾行填入 agents/{AGENT_NAME}/.env：")
    print(f"  AGENT_PORTFOLIO_ID={target.get('agentPortfolioId')}")
    print(f"  AGENT_USER_TOKEN_ID={token_id}")
    print(f"  AGENT_MIRROR_ID={target.get('mirrorId')}")


def main() -> int:
    print(f"Agent Portfolio 驗證工具  |  目標 Agent：{AGENT_NAME}")
    portfolios = test_main_list_agent_portfolios()
    agent_ok = test_agent_read_portfolio()
    suggest_metadata_to_fill(portfolios)

    print("\n" + "=" * 64)
    print("  總結")
    print("=" * 64)
    print(f"  主帳戶列表 Agent Portfolio : {'[OK]' if portfolios else '[FAIL]'}")
    print(f"  Agent 讀自己 demo 帳戶     : {'[OK]' if agent_ok else '[FAIL]'}")
    print()
    return 0 if portfolios and agent_ok else 1


if __name__ == "__main__":
    sys.exit(main())
