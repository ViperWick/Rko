import json
import re
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path


def _now_ms() -> int:
    return int(time.time() * 1000)


def _log_ndjson(log_path: Path, payload: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _check_url(url: str, timeout_s: int = 15) -> tuple[str, str]:
    """
    Returns (status, info)
    - status: HTTP status code as string, or 'ERR'
    - info: final URL after redirects, or exception info
    """
    headers = {"User-Agent": "cursor-link-check/1.0"}

    # Some servers disallow HEAD; try HEAD then GET.
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                return str(getattr(r, "status", "200")), str(r.geturl())
        except urllib.error.HTTPError as e:
            # HTTPError has a code (e.g., 404) and still may provide a URL
            return str(getattr(e, "code", "ERR")), f"HTTPError: {e}"
        except Exception as e:
            last_exc = e
            continue
    return "ERR", f"{type(last_exc).__name__}: {last_exc}"


def extract_hrefs_from_html(html_text: str) -> list[str]:
    urls = re.findall(r'href="(https?://[^"]+)"', html_text)
    urls = [unescape(u).strip() for u in urls]
    # preserve order unique
    seen = set()
    out = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    html_path = repo_root / "量子計算" / "量子計算採購清單_視覺化.html"
    log_path = repo_root / ".cursor" / "debug.log"

    run_id = f"linkcheck-{_now_ms()}"
    hypothesis_id = "L404"

    html_text = html_path.read_text(encoding="utf-8")
    urls = extract_hrefs_from_html(html_text)

    # also include the user-provided example for comparison
    extra = "https://www.youtube.com/watch?v=jlKta9yScQw"
    if extra not in urls:
        urls.append(extra)

    _log_ndjson(
        log_path,
        {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": "tools/link_check.py:main",
            "message": "start",
            "data": {"count": len(urls), "html": str(html_path)},
            "timestamp": _now_ms(),
        },
    )

    bad = 0
    for idx, url in enumerate(urls, start=1):
        status, info = _check_url(url)
        is_bad = status in {"404", "ERR"}
        bad += 1 if is_bad else 0
        _log_ndjson(
            log_path,
            {
                "sessionId": "debug-session",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": "tools/link_check.py:check",
                "message": "checked",
                "data": {"i": idx, "url": url, "status": status, "info": info, "bad": is_bad},
                "timestamp": _now_ms(),
            },
        )

    _log_ndjson(
        log_path,
        {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": "tools/link_check.py:main",
            "message": "done",
            "data": {"count": len(urls), "bad": bad},
            "timestamp": _now_ms(),
        },
    )

    print(f"Checked {len(urls)} urls, bad={bad}. runId={run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


