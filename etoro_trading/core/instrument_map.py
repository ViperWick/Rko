# -*- coding: utf-8 -*-
"""
Instrument ID 對照模組
查不到的 ID 會向 eToro API 查詢，並自動寫入 instrument_ids.json 作為本地資料庫
"""
import json
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INST_MAP_FILE = DATA_DIR / "instrument_ids.json"


def load_local_map() -> dict:
    """載入本地 instrument_ids.json"""
    if not INST_MAP_FILE.exists():
        return {}
    return json.loads(INST_MAP_FILE.read_text(encoding="utf-8"))


def save_map(inst_map: dict) -> None:
    """儲存對照表到 instrument_ids.json"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INST_MAP_FILE.write_text(json.dumps(inst_map, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_ids(client, instrument_ids: list[int]) -> tuple[dict, dict]:
    """
    解析 instrument_id → symbol, instrument_id → name
    先查本地 instrument_ids.json，查不到的向 API 查詢並寫回
    回傳 (id_to_symbol, id_to_name)
    """
    id_to_symbol = {}
    id_to_name = {}
    inst_map = load_local_map()

    for iid in instrument_ids:
        key = str(iid)
        if key in inst_map:
            arr = inst_map[key]
            id_to_symbol[iid] = arr[0] if isinstance(arr, list) else arr
            id_to_name[iid] = arr[1] if isinstance(arr, list) and len(arr) > 1 else ""

    unknown = [x for x in instrument_ids if x not in id_to_symbol]
    if unknown and client:
        before_count = len(inst_map)
        for iid in unknown:
            try:
                meta = client.get_instruments_metadata([iid])
                if meta:
                    m = meta[0]
                    sym = m.get("symbolFull") or m.get("instrumentDisplayName") or str(iid)
                    name = m.get("instrumentDisplayName") or ""
                    id_to_symbol[iid] = sym
                    id_to_name[iid] = name
                    inst_map[str(iid)] = [sym, name]
            except Exception:
                pass
            time.sleep(1.0)
        if len(inst_map) > before_count:
            save_map(inst_map)

    return id_to_symbol, id_to_name
