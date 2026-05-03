"""
「手腳」：Agent 只能呼叫這裡註冊的函式。
新增工具時：1) 寫函式 2) 加入 TOOL_REGISTRY 3) 在 agent.py 的 SYSTEM 補一句說明。
"""
from __future__ import annotations

import json
from pathlib import Path

# 只允許讀此目錄底下，避免任意讀檔
_SAFE_ROOT = Path(__file__).resolve().parent


def read_text_file(relative_path: str, max_chars: int = 8000) -> str:
    """讀取專案 demo 目錄內的文字檔（utf-8）。"""
    path = (_SAFE_ROOT / relative_path).resolve()
    if _SAFE_ROOT not in path.parents and path != _SAFE_ROOT:
        return json.dumps({"error": "path_not_allowed", "hint": "只能讀 local_agent_demo 底下的路徑"})
    if not path.is_file():
        return json.dumps({"error": "not_a_file", "path": str(path)})
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... (已截斷，共 {max_chars} 字元)"
    return text


def count_text_stats(text: str) -> str:
    """統計字元數、行數、非空白字元數（不讀檔，直接吃字串）。"""
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    non_ws = sum(1 for c in text if not c.isspace())
    return json.dumps(
        {
            "chars": len(text),
            "lines": lines,
            "non_whitespace_chars": non_ws,
        },
        ensure_ascii=False,
    )


TOOL_REGISTRY: dict[str, callable] = {
    "read_text_file": read_text_file,
    "count_text_stats": count_text_stats,
}


def run_tool(name: str, args: dict) -> str:
    if name not in TOOL_REGISTRY:
        return json.dumps({"error": "unknown_tool", "name": name})
    fn = TOOL_REGISTRY[name]
    try:
        result = fn(**args)
        return result if isinstance(result, str) else str(result)
    except TypeError as e:
        return json.dumps({"error": "bad_args", "detail": str(e)})
    except Exception as e:
        return json.dumps({"error": "tool_failed", "detail": str(e)})
