# -*- coding: utf-8 -*-
"""
建立 Instrument ID 對照表（會呼叫 API，需約 1.5 秒/標的）
執行: python -m etoro_trading.scripts.build_instrument_map
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAP_FILE = DATA_DIR / "instrument_ids.json"

# 要建立的標的清單（可自行擴充，含投資組合截圖中的標的）
SYMBOLS = [
    "BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "LTC", "AVAX", "LINK", "DOT", "MATIC", "UNI", "AAVE",
    "AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "NFLX", "AMD", "INTC", "JPM", "V", "MA",
    "DIS", "COIN", "MSTR", "PYPL", "SQ", "UBER", "ABNB", "SHOP", "CRM", "ORCL", "ADBE", "NKE", "WMT",
    "HD", "JNJ", "PFE", "XOM", "CVX", "BA", "CAT", "DE", "GE", "F", "GM", "T", "VZ", "KO", "PEP", "MCD", "SBUX",
    "NEE", "XEL", "SO", "DUK", "D", "AEP", "SRE", "WEC", "ES", "EIX", "ED", "DTE", "PEG", "AWK", "CNP",
    "SPY", "QQQ", "VOO", "IWM", "GLD", "SLV", "TLT",
    # 投資組合截圖中的標的
    "U", "ETOR", "ZM", "QBTS", "NEAR", "VST", "AFRM", "FET", "FMC", "STRK", "CRIS", "UUUU", "SUI",
    "IONQ", "RGTI", "SMR", "OKLO", "LUNR", "QUBT", "QSI", "APP", "RKLB", "HOOD", "CHPT", "SOFI", "TEAM",
    "HBAR", "ALGO", "BNGO", "URA", "TTWO", "RDDT", "CQQQ", "DDD", "AMPX", "GEMI", "CLSK", "XLM",
    "CLOU", "TRX", "ARKF", "COPX", "AREC", "PLTR", "NXPI", "SIDU", "DHR", "EXP", "TQQQ", "OCGN",
    # 更多截圖標的（股票、ETF、歐股等）
    "IBM", "UNH", "VIE.PA", "ACN", "HON", "RSG", "MRVL", "RR.L", "RHM.DE", "UMI.BR",
    "SE", "RACE", "TMUS", "KBWB", "HIMS", "SGM.ASX", "RBLX", "CLH", "QYLD", "RIOT", "GFL", "OXIG.L", "SES",
    "SPCE", "ARKK", "ARKX", "PAVE", "ATOM", "QNT", "IGV", "TRUMP", "SOXL", "DJT", "BOTZ",
    "XYLD", "RYLD", "JEPQ", "CPER", "TNA", "SKYY", "NOK", "IFRA", "ERIC", "AOS", "INDA", "IWN", "EEM",
    # 分散板塊（與科技相關性低）
    "XLU", "XLE", "XLP", "XLV", "PG",
]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if MAP_FILE.exists():
        existing = json.loads(MAP_FILE.read_text(encoding="utf-8"))

    try:
        from etoro_trading.core.etoro_client import EToroClient
        client = EToroClient()
    except Exception as e:
        print(f"連線失敗: {e}")
        return 1

    print(f"已載入 {len(existing)} 筆對照，開始擴充...")
    updated = 0
    for i, s in enumerate(SYMBOLS):
        try:
            inst = client.search_instrument(s)
            if inst:
                iid = inst.get("instrumentId") or inst.get("instrumentID")
                name = inst.get("instrumentDisplayName") or inst.get("internalSymbolFull", s)
                key = str(iid)
                if key not in existing:
                    existing[key] = [s, name]
                    updated += 1
                    print(f"  + {s} -> ID {iid} ({name})")
            time.sleep(1.5)
        except Exception as e:
            print(f"  Skip {s}: {e}")
        if (i + 1) % 10 == 0:
            print(f"  進度: {i+1}/{len(SYMBOLS)}")

    MAP_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完成！共 {len(existing)} 筆，新增 {updated} 筆，已儲存至 {MAP_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
