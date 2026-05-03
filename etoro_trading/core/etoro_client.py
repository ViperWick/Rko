# -*- coding: utf-8 -*-
"""
eToro API 客戶端
封裝所有 API 呼叫
"""
import uuid
import requests
from .config import get_config


class EToroClient:
    """eToro API 客戶端"""

    def __init__(self, api_key=None, user_key=None):
        if api_key and user_key:
            self.api_key = api_key
            self.user_key = user_key
            self.mode = "real"
            self.base_url = "https://public-api.etoro.com"
        else:
            config = get_config()
            self.api_key = config["api_key"]
            self.user_key = config["user_key"]
            self.mode = config["mode"]
            self.base_url = config["base_url"]
        self._instrument_cache = {}

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "x-user-key": self.user_key,
            "x-request-id": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }

    def _trading_prefix(self):
        """Demo 與 Real 的 API 路徑前綴"""
        return "demo" if self.mode == "demo" else ""

    def _execution_path(self, endpoint):
        if self.mode == "demo":
            return f"/api/v1/trading/execution/demo/{endpoint}"
        return f"/api/v1/trading/execution/{endpoint}"

    def _info_path(self, endpoint):
        # Demo: /api/v1/trading/info/demo/pnl
        # Real: /api/v1/trading/info/real/pnl
        mode = "demo" if self.mode == "demo" else "real"
        return f"/api/v1/trading/info/{mode}/{endpoint}"

    # ========== 市場數據 ==========

    def search_instrument(self, symbol: str) -> dict | None:
        """搜尋標的，取得 Instrument ID"""
        if symbol.upper() in self._instrument_cache:
            return self._instrument_cache[symbol.upper()]

        url = f"{self.base_url}/api/v1/market-data/search"
        params = {"internalSymbolFull": symbol.upper()}
        resp = requests.get(url, headers=self._headers(), params=params)

        if resp.status_code != 200:
            raise Exception(f"搜尋失敗: {resp.status_code} - {resp.text}")

        data = resp.json()
        items = data.get("items", [])
        instrument = next(
            (i for i in items if i.get("internalSymbolFull") == symbol.upper()), None
        )

        if instrument:
            self._instrument_cache[symbol.upper()] = instrument
        return instrument

    def get_instrument_id(self, symbol: str) -> int:
        """取得標的的 Instrument ID"""
        inst = self.search_instrument(symbol)
        if not inst:
            raise ValueError(f"找不到標的: {symbol}")
        return inst["instrumentId"]

    def get_instruments_metadata(self, instrument_ids: list[int]) -> list[dict]:
        """取得多個標的的元數據（名稱、代碼等）"""
        if not instrument_ids:
            return []
        url = f"{self.base_url}/api/v1/market-data/instruments"
        params = {"instrumentIds": ",".join(str(i) for i in instrument_ids[:100])}
        resp = requests.get(url, headers=self._headers(), params=params)
        if resp.status_code != 200:
            raise Exception(f"取得元數據失敗: {resp.status_code} - {resp.text}")
        data = resp.json()
        return data.get("instrumentDisplayDatas", [])

    def get_candles(
        self,
        instrument_id: int,
        interval: str = "OneDay",
        count: int = 365,
        direction: str = "desc",
    ) -> list[dict]:
        """
        取得歷史 K 線（OHLCV）
        interval: OneMinute, FiveMinutes, TenMinutes, FifteenMinutes, ThirtyMinutes,
                  OneHour, FourHours, OneDay, OneWeek
        count: 最多 1000
        direction: asc（舊→新）或 desc（新→舊）
        """
        url = f"{self.base_url}/api/v1/market-data/instruments/{instrument_id}/history/candles/{direction}/{interval}/{count}"
        resp = requests.get(url, headers=self._headers())
        if resp.status_code != 200:
            raise Exception(f"取得 K 線失敗: {resp.status_code} - {resp.text}")
        data = resp.json()
        items = data.get("candles", [])
        if not items:
            return []
        # 回傳格式: [{instrumentId, candles: [{fromDate, open, high, low, close, volume}, ...]}]
        first = items[0]
        return first.get("candles", [])

    # ========== 資產查詢 ==========

    def get_portfolio(self) -> dict:
        """取得投資組合（餘額、持倉、訂單、PnL）"""
        url = f"{self.base_url}{self._info_path('pnl')}"
        resp = requests.get(url, headers=self._headers())

        if resp.status_code != 200:
            raise Exception(f"取得投資組合失敗: {resp.status_code} - {resp.text}")

        return resp.json()

    def get_daily_gain(
        self,
        username: str,
        min_date: str,
        max_date: str,
        period_type: str = "Daily",
    ) -> list | dict:
        """
        取得指定日期區間的每日/區間損益（user-info API）
        username: 帳戶用戶名（eToro 顯示名稱）
        min_date / max_date: YYYY-MM-DD
        period_type: 'Daily' 回傳每日陣列，'Period' 回傳整段期間合計
        回傳: Daily 時為 [{timestamp, gain}, ...]，Period 時為 {gain: number}
        """
        url = f"{self.base_url}/api/v1/user-info/people/{username}/daily-gain"
        params = {
            "minDate": min_date,
            "maxDate": max_date,
            "type": period_type,
        }
        resp = requests.get(url, headers=self._headers(), params=params)
        if resp.status_code != 200:
            raise Exception(f"取得每日績效失敗: {resp.status_code} - {resp.text}")
        return resp.json()

    # ========== 下單 ==========

    def open_position_by_amount(
        self,
        symbol: str,
        amount: float,
        is_buy: bool = True,
        leverage: int = 1,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> dict:
        """依金額開倉（市價單）"""
        instrument_id = self.get_instrument_id(symbol)
        url = f"{self.base_url}{self._execution_path('market-open-orders/by-amount')}"

        payload = {
            "InstrumentID": instrument_id,
            "Amount": amount,
            "IsBuy": is_buy,
            "Leverage": leverage,
        }
        if stop_loss is not None:
            payload["StopLossRate"] = stop_loss
            payload["IsNoStopLoss"] = False
        else:
            payload["IsNoStopLoss"] = True
        if take_profit is not None:
            payload["TakeProfitRate"] = take_profit
            payload["IsNoTakeProfit"] = False
        else:
            payload["IsNoTakeProfit"] = True

        resp = requests.post(url, headers=self._headers(), json=payload)

        if resp.status_code != 200:
            raise Exception(f"下單失敗: {resp.status_code} - {resp.text}")

        return resp.json()

    def close_position(self, position_id: int, units_to_deduct: float | None = None) -> dict:
        """平倉（全部或部分）"""
        url = f"{self.base_url}{self._execution_path(f'market-close-orders/positions/{position_id}')}"
        payload = {"UnitsToDeduct": units_to_deduct}
        resp = requests.post(url, headers=self._headers(), json=payload)

        if resp.status_code != 200:
            raise Exception(f"平倉失敗: {resp.status_code} - {resp.text}")

        return resp.json()
