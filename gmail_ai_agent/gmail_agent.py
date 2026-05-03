"""
Gmail + LLM：拉取近期郵件 → 分類與摘要 → 可選套用 Gmail 標籤。

首次使用：
1. Google Cloud Console 建立專案 → 啟用 Gmail API → 建立「桌面應用程式」OAuth 用戶端 → 下載 credentials.json 放在本目錄。
2. pip install -r requirements.txt
3. 摘要預設用本機 Ollama（OpenAI 相容 API）：先安裝並執行 ollama serve，並 ollama pull 你的模型（預設 llama3.2）。
   可選環境變數：OLLAMA_BASE_URL、OLLAMA_MODEL、OLLAMA_API_KEY（本機可填任意字串）。
4. 若要改用 OpenAI 雲端：設定 OPENAI_API_KEY，並加參數 --llm openai（或環境變數 GMAIL_LLM=openai）。
5. python gmail_agent.py --once

每日自動：用 Windows 工作排程器執行同上指令（或 --apply-labels 若已改 scopes）。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = DIR / "credentials.json"
TOKEN_FILE = DIR / "token.json"

# 僅讀取：readonly。若要自動貼標籤，改成 SCOPES_MODIFY 並刪除舊 token.json 重新授權。
SCOPES_READONLY = ["https://www.googleapis.com/auth/gmail.readonly"]
SCOPES_MODIFY = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service(allow_modify: bool):
    scopes = SCOPES_MODIFY if allow_modify else SCOPES_READONLY
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(
                    f"缺少 {CREDENTIALS_FILE}。請從 Google Cloud Console 下載 OAuth 用戶端 JSON。",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), scopes)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def _decode_part_body(data: str | None) -> str:
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        return ""


def extract_plain_text(payload: dict) -> str:
    """盡量從 Gmail message payload 抽出純文字（過長會在呼叫端截斷）。"""
    if not payload:
        return ""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    if mime == "text/plain" and body.get("data"):
        return _decode_part_body(body.get("data"))
    parts = payload.get("parts") or []
    for p in parts:
        if p.get("mimeType") == "text/plain" and p.get("body", {}).get("data"):
            return _decode_part_body(p["body"]["data"])
    for p in parts:
        if p.get("parts"):
            inner = extract_plain_text(p)
            if inner:
                return inner
    if mime == "text/html" and body.get("data"):
        # 粗略：當沒有 plain 時退回 HTML 原文（給 LLM 仍常有幫助）
        return _decode_part_body(body.get("data"))
    for p in parts:
        if p.get("mimeType") == "text/html" and p.get("body", {}).get("data"):
            return _decode_part_body(p["body"]["data"])
    return ""


def fetch_recent_messages(service, query: str, max_results: int) -> list[dict]:
    resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    mids = [m["id"] for m in resp.get("messages", [])]
    out = []
    for mid in mids:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=mid, format="full")
            .execute()
        )
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        text = extract_plain_text(msg.get("payload", {}))
        out.append(
            {
                "id": mid,
                "threadId": msg.get("threadId"),
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "date": headers.get("date", ""),
                "snippet": msg.get("snippet", ""),
                "body": text[:12000],
            }
        )
    return out


def run_llm(messages: list[dict], model: str, *, backend: str) -> dict:
    if OpenAI is None:
        raise RuntimeError("請安裝 openai：pip install openai")

    if backend == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        api_key = os.environ.get("OLLAMA_API_KEY", "ollama")
        client = OpenAI(base_url=base_url, api_key=api_key)
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("使用 OpenAI 時請設定環境變數 OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
    brief = [
        {
            "id": m["id"],
            "subject": m["subject"],
            "from": m["from"],
            "snippet": m["snippet"],
            "body_preview": (m["body"] or "")[:4000],
        }
        for m in messages
    ]
    system = """你是郵件助理。請根據輸入的郵件列表輸出嚴格 JSON（不要 markdown），格式：
{
  "summary": "當日信箱一句話總結",
  "items": [
    {
      "id": "<與輸入相同>",
      "category": "工作|財務|社群|行銷|訂閱|重要人事|其他 擇一",
      "priority": "高|中|低",
      "one_line": "中文一行摘要",
      "suggested_action": "建議動作或無"
    }
  ]
}
分類要一致；若內容不足，one_line 可簡短。"""
    user = json.dumps(brief, ensure_ascii=False)
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    raw = (r.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def ensure_label(service, name: str) -> str:
    lst = service.users().labels().list(userId="me").execute().get("labels", [])
    for lb in lst:
        if lb.get("name") == name and lb.get("type") == "user":
            return lb["id"]
    body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    created = service.users().labels().create(userId="me", body=body).execute()
    return created["id"]


def apply_category_labels(service, items: list[dict], id_to_msg: dict[str, dict]):
    """依 LLM 的 category 建立/使用使用者標籤並加到郵件上。"""
    cat_to_label_id: dict[str, str] = {}
    for it in items:
        mid = it.get("id")
        cat = (it.get("category") or "其他").strip()
        if not mid:
            continue
        if cat not in cat_to_label_id:
            cat_to_label_id[cat] = ensure_label(service, f"AI-{cat}")
        label_id = cat_to_label_id[cat]
        service.users().messages().modify(
            userId="me",
            id=mid,
            body={"addLabelIds": [label_id]},
        ).execute()


def main():
    parser = argparse.ArgumentParser(description="Gmail AI 分類/摘要")
    parser.add_argument(
        "--query",
        default="newer_than:1d",
        help='Gmail 搜尋式，預設最近一天（例：newer_than:7d category:primary）',
    )
    parser.add_argument("--max", type=int, default=40, help="最多處理幾封")
    parser.add_argument(
        "--apply-labels",
        action="store_true",
        help="依分類套用 Gmail 標籤（需 gmail.modify，首次請刪除 token.json 重授權）",
    )
    parser.add_argument("--output", type=Path, help="將 JSON 結果寫入檔案")
    parser.add_argument("--once", action="store_true", help="執行一次後結束（給排程用）")
    parser.add_argument(
        "--llm",
        choices=("ollama", "openai"),
        default=os.environ.get("GMAIL_LLM", "ollama"),
        help="摘要後端：ollama=本機預設；openai=需 OPENAI_API_KEY（預設可改環境變數 GMAIL_LLM）",
    )
    args = parser.parse_args()

    if args.llm == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    else:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    service = get_gmail_service(allow_modify=args.apply_labels)

    messages = fetch_recent_messages(service, args.query, args.max)
    if not messages:
        print("沒有符合條件的郵件。")
        return

    result = run_llm(messages, model=model, backend=args.llm)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)

    if args.output:
        args.output.write_text(text, encoding="utf-8")

    if args.apply_labels and result.get("items"):
        id_map = {m["id"]: m for m in messages}
        apply_category_labels(service, result["items"], id_map)
        print("已套用標籤。", file=sys.stderr)


if __name__ == "__main__":
    main()
