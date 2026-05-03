# -*- coding: utf-8 -*-
"""
eToro 交易程式 - 設定模組
金鑰從環境變數讀取，絕不寫入程式碼
"""
import os
from pathlib import Path

# etoro_trading 套件根目錄（.env 放這裡）
_CONFIG_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv():
    """載入 .env，優先從 etoro_trading 目錄讀取"""
    candidates = [
        _CONFIG_DIR / ".env",                        # etoro_trading/.env
        _CONFIG_DIR.parent / "etoro_trading" / ".env",
        Path.cwd() / "etoro_trading" / ".env",
        Path.cwd() / ".env",
    ]
    env_path = None
    for p in candidates:
        if p.exists():
            env_path = p
            break
    if not env_path:
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except Exception:
        pass
    # 若 dotenv 未設定成功，改用手動讀取 .env（避免編碼/BOM 等問題）
    api_key = os.getenv("ETORO_API_KEY") or os.getenv("ETORO_USER_KEY")
    user_key = os.getenv("ETORO_USER_KEY") or os.getenv("ETORO_API_KEY")
    if api_key and user_key:
        return
    try:
        raw = env_path.read_text(encoding="utf-8-sig").strip()
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in ("ETORO_API_KEY", "ETORO_USER_KEY", "ETORO_MODE", "ETORO_USERNAME") and v:
                os.environ.setdefault(k, v)
    except Exception:
        pass


def get_config():
    """取得 API 設定"""
    _load_dotenv()
    api_key = os.getenv("ETORO_API_KEY") or os.getenv("ETORO_USER_KEY")
    user_key = os.getenv("ETORO_USER_KEY") or os.getenv("ETORO_API_KEY")
    mode = os.getenv("ETORO_MODE", "real").lower()

    if not api_key or not user_key:
        env_path = _CONFIG_DIR / ".env"
        hint = f"請確認 {env_path} 存在且含有 ETORO_API_KEY、ETORO_USER_KEY。"
        raise ValueError(
            "請設定 ETORO_API_KEY 和 ETORO_USER_KEY 環境變數。\n"
            "複製 .env.example 為 .env 並填入您的金鑰。\n" + hint
        )

    return {
        "api_key": api_key,
        "user_key": user_key,
        "mode": "demo" if mode == "demo" else "real",
        "base_url": "https://public-api.etoro.com",
        "username": os.getenv("ETORO_USERNAME", "").strip() or None,  # 選填，用於每日績效 API
    }
