"""
每週宏觀快照：從 FRED 拉最近幾筆觀測值（需免費 API Key）。
無 FRED 金鑰時仍會列印官方連結。有 FRED 金鑰時另拉：T10YIE、T10Y2Y、VIXCLS、NFCI、
WALCL、Henry Hub（`DHHNGSP`）等（與檢查表 §6.1／Canvas 擴充區一致）。
若有 EIA 金鑰則另取得：WTI（RWTC）、月度核能淨發電（`ELEC.GEN.NUC-US-99.M`）、
全美核能停機（`us-nuclear-outages`，優先 `percentOutage`）。

註冊：FRED https://fred.stlouisfed.org/docs/api/api_key.html
      EIA https://www.eia.gov/opendata/register.php

用法（擇一）：
  A) PowerShell：$env:FRED_API_KEY / $env:EIA_API_KEY
  B) 建議：同目錄 secrets.env（勿提交 git），見 secrets.env.example

  py .\\run_weekly_snapshot.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
EIA_V2 = "https://api.eia.gov/v2/"
EIA_WTI_URL = f"{EIA_V2}petroleum/pri/spt/data/"

# APIv1 系列經 v2 /seriesid 轉譯：美國各業別核能淨發電量（月度，通常為百萬千瓦時）
EIA_SERIES_NUC_GEN_MONTHLY = "ELEC.GEN.NUC-US-99.M"

# 系列說明見檢查表 Markdown；前 3 項為「核心」，其餘為擴充（同一支 FRED API Key）
SERIES = [
    ("DGS10", "美國 10 年期公債殖利率 (%)"),
    ("DTWEXBGS", "廣義美元指數 (Goods and Services, Index)"),
    ("BAMLH0A0HYM2", "美國高收益債 OAS (%)"),
    ("T10YIE", "10 年期盈虧平衡通膨率 (%)"),
    ("T10Y2Y", "10 年與 2 年殖利率利差 (%)"),
    ("VIXCLS", "VIX 波動率指數"),
    ("NFCI", "芝加哥聯準全國金融狀況指數 NFCI"),
    ("WALCL", "聯準會總資產 WALCL (百萬美元)"),
    ("DHHNGSP", "Henry Hub 天然氣現貨 (美元/MMBtu)"),
]

SERIES_CORE_COUNT = 3

def load_secrets_env() -> None:
    """從腳本同目錄的 secrets.env 讀入 FRED_API_KEY / EIA_API_KEY（不覆寫已存在環境變數）。"""
    env_path = Path(__file__).resolve().parent / "secrets.env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


MANUAL_LINKS = """
【手動核對】EIA 發電量／燃料結構：
  https://www.eia.gov/electricity/data.php
EIA 核能總覽（發電／停機等）：
  https://www.eia.gov/nuclear/
IAEA PRIS（全球核電機組）：
  https://pris.iaea.org/
WNA 產業整理：
  https://world-nuclear.org/
ETF 資金流工具（示例）：
  https://www.etf.com/etfanalytics/etf-fund-flows-tool
完整每週表（含核能第八節）：tools/weekly_market_check/每週市場與能源檢查表.md
"""


def fetch_fred(series_id: str, api_key: str, limit: int = 5) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": str(limit),
        }
    )
    url = f"{FRED_BASE}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "weekly_market_check/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return list(payload.get("observations", []))


def eia_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "weekly_market_check/1.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_eia_wti_recent(api_key: str, length: int = 5) -> list[dict]:
    """EIA v2 範例：WTI 現貨 Cushing（series=RWTC），驗證金鑰並示範 JSON 結構。"""
    params = urllib.parse.urlencode(
        {
            "api_key": api_key,
            "frequency": "daily",
            "data[0]": "value",
            "facets[series][]": "RWTC",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": str(length),
        }
    )
    url = f"{EIA_WTI_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "weekly_market_check/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    resp_obj = payload.get("response") or {}
    return list(resp_obj.get("data") or [])


def fetch_eia_v2_data_rows(route: str, api_key: str, params: list[tuple[str, str]]) -> list[dict]:
    """route 例：nuclear-outages/us-nuclear-outages/data/（勿前置斜線）。"""
    path = route.removeprefix("/")
    if not path.endswith("/"):
        path += "/"
    q: list[tuple[str, str]] = [("api_key", api_key), *params]
    qs = urllib.parse.urlencode(q, doseq=True)
    url = f"{EIA_V2}{path}?{qs}"
    payload = eia_get_json(url)
    resp = payload.get("response") or {}
    return list(resp.get("data") or [])


def fetch_eia_seriesid_recent(series_id: str, api_key: str, length: int = 6) -> list[dict]:
    """以 APIv1 Series ID 經 v2 /seriesid 取觀測值（期別由 API 決定）。"""
    sid = urllib.parse.quote(series_id, safe=".")
    params = urllib.parse.urlencode(
        {
            "api_key": api_key,
            "length": str(length),
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
        }
    )
    url = f"{EIA_V2}seriesid/{sid}?{params}"
    payload = eia_get_json(url)
    resp = payload.get("response") or {}
    return list(resp.get("data") or [])


def fetch_us_nuclear_outages_daily(api_key: str, length: int = 7) -> tuple[list[dict], str]:
    """
    美國整體核能停機（日頻）。EIA 欄位代碼為 capacity / outage / percentOutage（camelCase）。
    回傳 (列資料, 所用 data 欄位代碼)。
    """
    route = "nuclear-outages/us-nuclear-outages/data/"
    common = [
        ("frequency", "daily"),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "desc"),
        ("length", str(length)),
    ]
    last_http: urllib.error.HTTPError | None = None
    for data_col in ("percentOutage", "outage"):
        try:
            rows = fetch_eia_v2_data_rows(
                route,
                api_key,
                [("data[]", data_col), *common],
            )
            if rows:
                return rows, data_col
        except urllib.error.HTTPError as e:
            last_http = e
            continue
    if last_http is not None:
        raise last_http
    return [], "percentOutage"


def print_series(name: str, title: str, rows: list[dict]) -> None:
    print(f"\n=== {name} — {title} ===")
    printed = 0
    for row in rows:
        val = row.get("value")
        if val in (".", None, ""):
            continue
        print(f"  {row.get('date')}: {val}")
        printed += 1
        if printed >= 5:
            break
    if printed == 0:
        print("  （最近幾筆皆為缺值 . ，請改上 FRED 網頁查看）")


def print_eia_nuclear_rows(label: str, rows: list[dict], value_hint: str | None = None) -> None:
    """印 EIA v2 列：優先 value_hint、value、generation、percentOutage 等，略過 sectorid 等雜訊。"""
    print(f"\n=== {label} ===")
    if not rows:
        print("  （無資料列）")
        return
    skip_keys = {
        "period",
        "date",
        "location",
        "stateDescription",
        "sectorid",
        "sectorDescription",
        "fueltypeid",
        "fuelTypeDescription",
    }
    take = 0
    for row in rows:
        period = row.get("period") or row.get("date") or "?"
        val = None
        used_key = value_hint
        for key in (value_hint, "value", "generation", "percentOutage", "outage", "capacity"):
            if key and row.get(key) is not None:
                val = row.get(key)
                used_key = key
                break
        if val is None:
            for k, v in row.items():
                if k in skip_keys or k.endswith("-units") or k.endswith("Description"):
                    continue
                if isinstance(v, (int, float)):
                    val, used_key = v, k
                    break
        extra: list[str] = []
        if used_key and row.get(f"{used_key}-units"):
            extra.append(str(row.get(f"{used_key}-units")))
        u = f" ({extra[0]})" if extra else ""
        print(f"  {period}: {val}{u}")
        take += 1
        if take >= 6:
            break


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    load_secrets_env()
    fred_key = os.environ.get("FRED_API_KEY", "").strip()
    eia_key = os.environ.get("EIA_API_KEY", "").strip()

    print("每週快照：FRED（宏觀）＋可選 EIA（能源 API 測試）\n")

    if not fred_key:
        print("未設定 FRED_API_KEY（secrets.env 或環境變數），略過 FRED 拉取。\n")
        print("請到 FRED 申請後填入 secrets.env，下列為本腳本會用的系列：\n")
        for sid, title in SERIES:
            print(f"  {sid}: https://fred.stlouisfed.org/series/{sid}")
    else:
        for idx, (sid, title) in enumerate(SERIES):
            if idx == 0:
                print("=== FRED：核心三項（DGS10／美元／HY OAS）===")
            if idx == SERIES_CORE_COUNT:
                print(
                    "\n=== FRED 擴充（T10YIE／曲線／VIX／NFCI／資產表／Henry Hub）==="
                )
            try:
                obs = fetch_fred(sid, fred_key, limit=8)
                print_series(sid, title, obs)
            except urllib.error.HTTPError as e:
                print(f"\n=== {sid} ===\n  HTTP 錯誤: {e.code} {e.reason}", file=sys.stderr)
            except urllib.error.URLError as e:
                print(f"\n=== {sid} ===\n  連線錯誤: {e.reason}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"\n=== {sid} ===\n  錯誤: {e}", file=sys.stderr)

    if eia_key:
        print("\n=== EIA API：WTI 現貨 RWTC（最近幾日，驗證金鑰）===")
        try:
            rows = fetch_eia_wti_recent(eia_key, length=5)
            for row in rows[:5]:
                p = row.get("period")
                v = row.get("value")
                print(f"  {p}: {v}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            print(f"  HTTP {e.code}: {e.reason}\n  {body}", file=sys.stderr)
        except urllib.error.URLError as e:
            print(f"  連線錯誤: {e.reason}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  錯誤: {e}", file=sys.stderr)

        print("\n=== EIA API：美國核能淨發電（月度，seriesid）===")
        print(f"  系列: {EIA_SERIES_NUC_GEN_MONTHLY}（單位見 API 回傳）")
        try:
            nuc_rows = fetch_eia_seriesid_recent(EIA_SERIES_NUC_GEN_MONTHLY, eia_key, length=6)
            print_eia_nuclear_rows(
                "月度核能淨發電（最近幾個月，thousand MWh）",
                nuc_rows,
                value_hint="generation",
            )
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            print(f"  HTTP {e.code}: {e.reason}\n  {body}", file=sys.stderr)
        except urllib.error.URLError as e:
            print(f"  連線錯誤: {e.reason}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  錯誤: {e}", file=sys.stderr)

        print("\n=== EIA API：美國整體核能停機（日頻，us-nuclear-outages）===")
        try:
            out_rows, used_col = fetch_us_nuclear_outages_daily(eia_key, length=7)
            print(f"  data 欄位: {used_col}")
            print_eia_nuclear_rows("最近幾日（percentOutage 或 outage）", out_rows, value_hint=used_col)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            print(f"  HTTP {e.code}: {e.reason}\n  {body}", file=sys.stderr)
        except urllib.error.URLError as e:
            print(f"  連線錯誤: {e.reason}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  錯誤: {e}", file=sys.stderr)
    else:
        print("\n未設定 EIA_API_KEY，略過 EIA 測試。")

    print(MANUAL_LINKS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
