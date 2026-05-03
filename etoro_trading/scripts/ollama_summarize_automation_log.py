# -*- coding: utf-8 -*-
"""
用本機 Ollama（OpenAI 相容 API）摘要「日常自動化」產生的 log。

前置：
  1. 安裝並啟動 Ollama：https://ollama.com
  2. 拉模型：ollama pull llama3.2   （或改環境變數 OLLAMA_MODEL）

執行（repo 根目錄）：
  py -m etoro_trading.scripts.ollama_summarize_automation_log
  py -m etoro_trading.scripts.ollama_summarize_automation_log --log path/to/daily_xxx.log

環境變數（可選，也可寫入 etoro_trading/.env）：
  OLLAMA_BASE_URL  預設 http://127.0.0.1:11434/v1
  OLLAMA_MODEL     預設 llama3.2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# 載入 .env（與專案其他腳本一致）
try:
    from dotenv import load_dotenv

    _ETORO = Path(__file__).resolve().parent.parent
    load_dotenv(_ETORO / ".env")
except Exception:
    pass


def _etoro_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _latest_log(log_dir: Path) -> Path | None:
    if not log_dir.is_dir():
        return None
    logs = sorted(log_dir.glob("daily_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def run_summarize(
    log_path: Path | None,
    base_url: str,
    model: str,
    timeout: int = 120,
) -> int:
    etoro = _etoro_root()
    log_dir = etoro / "data" / "automation_logs"
    out_dir = log_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if log_path is None:
        log_path = _latest_log(log_dir)
    if not log_path or not log_path.is_file():
        print("找不到 log。請先執行 run_daily_automation，或指定 --log", file=sys.stderr)
        return 1

    raw = log_path.read_text(encoding="utf-8", errors="replace")
    max_chars = int(os.environ.get("OLLAMA_LOG_MAX_CHARS", "14000"))
    if len(raw) > max_chars:
        raw = raw[:max_chars] + "\n\n[已截斷，僅送前 %d 字元]" % max_chars

    url = base_url.rstrip("/") + "/chat/completions"
    system = (
        "你是助理。請用繁體中文、條列簡短摘要下列「排程腳本」log："
        "1) 成功完成的步驟 2) 失敗或錯誤 3) 使用者明天可留意的一句。"
        "不要提供投資建議或買賣指令。"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "檔名: " + log_path.name + "\n\n---\n" + raw},
        ],
        "stream": False,
    }

    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as e:
        print("無法連線 Ollama：", e, file=sys.stderr)
        print("請確認 ollama serve 已執行，且 OLLAMA_BASE_URL 正確。", file=sys.stderr)
        return 1

    if r.status_code != 200:
        print("Ollama API 錯誤 HTTP", r.status_code, file=sys.stderr)
        print(r.text[:2000], file=sys.stderr)
        return 1

    try:
        data = r.json()
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print("無法解析回應：", e, file=sys.stderr)
        print(r.text[:2000], file=sys.stderr)
        return 1

    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"ollama_summary_{stamp}.md"
    header = f"# Ollama 摘要\n\n- 模型: `{model}`\n- 來源 log: `{log_path.name}`\n\n---\n\n"
    out_file.write_text(header + text.strip() + "\n", encoding="utf-8")
    print("已寫入:", out_file)
    print()
    print(text.strip())
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="用 Ollama 摘要 automation_logs 里的 daily log")
    p.add_argument("--log", type=Path, default=None, help="指定 log 路徑；預設取最新 daily_*.log")
    p.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
        help="OpenAI 相容 API 根路徑，預設 Ollama",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "llama3.2"),
        help="Ollama 模型名稱",
    )
    args = p.parse_args(argv)
    return run_summarize(args.log, args.base_url, args.model)


if __name__ == "__main__":
    sys.exit(main())
