"""
統計信箱內寄件人出現次數（Gmail API，唯讀）。

用法（在 gmail_ai_agent 目錄）：
  python gmail_sender_stats.py
  python gmail_sender_stats.py --query "newer_than:180d" --limit 2000

需已有 credentials.json、token.json。
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from email.utils import parseaddr

from gmail_agent import get_gmail_service


def extract_email_from_from_header(from_header: str) -> str:
    """從 From 標頭取出主要 email（小寫）。"""
    if not from_header:
        return "(無寄件者)"
    _, addr = parseaddr(from_header)
    if addr:
        return addr.strip().lower()
    # 備援：擷取第一個類似 email 的字串
    m = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", from_header)
    return m.group(0).lower() if m else from_header.strip()[:120]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gmail 寄件人統計")
    parser.add_argument(
        "--query",
        default="newer_than:365d",
        help="Gmail 搜尋條件（預設：近一年）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1500,
        help="最多處理幾封信（避免一次打太多 API）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=40,
        help="顯示前幾名寄件者",
    )
    args = parser.parse_args()

    service = get_gmail_service(allow_modify=False)
    user = "me"

    message_ids: list[str] = []
    page_token = None
    while len(message_ids) < args.limit:
        page = (
            service.users()
            .messages()
            .list(
                userId=user,
                q=args.query,
                maxResults=min(500, args.limit - len(message_ids)),
                pageToken=page_token,
            )
            .execute()
        )
        for m in page.get("messages", []):
            message_ids.append(m["id"])
            if len(message_ids) >= args.limit:
                break
        page_token = page.get("nextPageToken")
        if not page_token or len(message_ids) >= args.limit:
            break

    if not message_ids:
        print("沒有符合條件的郵件。", file=sys.stderr)
        return 1

    print(
        f"搜尋條件：{args.query}\n已取得 {len(message_ids)} 封，正在讀取寄件者…\n",
        file=sys.stderr,
    )

    counter: Counter[str] = Counter()
    for i, mid in enumerate(message_ids):
        msg = (
            service.users()
            .messages()
            .get(
                userId=user,
                id=mid,
                format="metadata",
                metadataHeaders=["From"],
            )
            .execute()
        )
        from_val = ""
        for h in msg.get("payload", {}).get("headers", []):
            if h.get("name", "").lower() == "from":
                from_val = h.get("value") or ""
                break
        key = extract_email_from_from_header(from_val)
        counter[key] += 1
        if (i + 1) % 200 == 0:
            print(f"  …已處理 {i + 1}/{len(message_ids)}", file=sys.stderr)

    total = sum(counter.values())
    unique = len(counter)
    print(f"統計範圍內共 {total} 封（不重複寄件者約 {unique} 個）\n")
    print(f"{'排名':<4} {'封數':>8}  寄件者 email")
    print("-" * 60)
    for rank, (sender, cnt) in enumerate(counter.most_common(args.top), start=1):
        print(f"{rank:<4} {cnt:>8}  {sender}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
