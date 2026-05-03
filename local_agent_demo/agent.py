"""
最小 Agent 迴圈：LLM 決定要「最終回答」或「呼叫工具」。
格式簡單，方便你先看懂框架；之後可改成 OpenAI 官方 tool_calls。

注意：底下的「openai」是免費的 Python 套件（pip install openai），只是 API 長得像 OpenAI。
我們在 config 裡把 base_url 指到本機 Ollama（127.0.0.1:11434），不會向 OpenAI 公司付費，
也不需要有效的 OpenAI API 金鑰。
"""
from __future__ import annotations

import json
import re
import sys

from openai import OpenAI  # 免費套件；連線目標由 OLLAMA_BASE_URL 決定（本機=免費）

from config import MAX_AGENT_STEPS, OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
from tools import run_tool

SYSTEM = """你是協助使用者的助理。你可以使用工具完成任務。

可用工具（用 JSON 參數呼叫）：
1) read_text_file — 參數: {"relative_path": "相對於 local_agent_demo 的檔案路徑，例如 README.md"}
2) count_text_stats — 參數: {"text": "要統計的一段文字"}

你每一則回覆必須是以下兩種之一（不要混雜其他內容）：

格式 A — 要呼叫工具：
TOOL: 工具名稱
ARGS: {"參數": "值"}

格式 B — 最終給使用者的答案：
FINAL: （這裡寫完整回答）

若還需要資訊，用格式 A；已足夠則用格式 B。"""


def parse_llm_reply(content: str) -> tuple[str, str | None, str | dict]:
    """回傳 (kind, tool_name, payload)。tool 時 payload 為 dict；final 時為 str。"""
    content = content.strip()
    if content.upper().startswith("FINAL:"):
        return "final", None, content[6:].strip()
    m = re.match(
        r"TOOL:\s*(\S+)\s*ARGS:\s*(\{.*\})\s*",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
        try:
            args = json.loads(m.group(2))
        except Exception:
            return "final", None, "模型給的 ARGS 不是合法 JSON，請簡短說明並請使用者重試。"
        return "tool", name, args
    # 無法解析時當作最終回答，避免卡死
    return "final", None, content


def main() -> None:
    user = " ".join(sys.argv[1:]).strip() or "請讀取 README.md，用 count_text_stats 統計前 500 字的行數與字元數，並用中文摘要結果。"
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]

    for step in range(MAX_AGENT_STEPS):
        r = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            temperature=0.2,
        )
        reply = (r.choices[0].message.content or "").strip()
        kind, tool_name, payload = parse_llm_reply(reply)

        if kind == "final" and tool_name is None:
            print(payload)
            return

        if kind == "tool" and tool_name and isinstance(payload, dict):
            observation = run_tool(tool_name, payload)
            messages.append({"role": "assistant", "content": reply})
            messages.append(
                {
                    "role": "user",
                    "content": f"工具執行結果如下，請繼續（TOOL/FINAL）：\n{observation}",
                }
            )
            continue

        # payload 在此分支是 str（最終文字）
        print(payload)
        return

    print("已達最大步數上限，請簡化任務或調高 MAX_AGENT_STEPS。")


if __name__ == "__main__":
    main()
