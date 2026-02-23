"""CoinMarketCap OHLCV downloader utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


CMC_BASE_URL = "https://pro-api.coinmarketcap.com"
SYMBOL_TO_PAIR = {
    "BTC": "btcusdt.p",
    "ETH": "ethusdt.p",
    "SOL": "solusdt.p",
    "XRP": "xrpusdt.p",
    "DOGE": "dogeusdt.p",
}


@dataclass(slots=True)
class CmcOhlcvClient:
    """Minimal CMC client to fetch historical OHLCV."""

    api_key: str
    timeout: int = 30
    _session: requests.Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._session = requests.Session()
        # Some environments inject blocked proxies by default.
        self._session.trust_env = False

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        headers = {"X-CMC_PRO_API_KEY": self.api_key, "Accept": "application/json"}
        response = self._session.get(
            f"{CMC_BASE_URL}{path}", headers=headers, params=params, timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status", {})
        if status.get("error_code", 0) != 0:
            raise RuntimeError(
                f"CMC API error {status.get('error_code')}: {status.get('error_message')}"
            )
        return payload

    def get_id_map(self, symbols: list[str]) -> dict[str, int]:
        payload = self._request("/v1/cryptocurrency/map", {"symbol": ",".join(symbols)})
        id_map: dict[str, int] = {}
        for item in payload.get("data", []):
            symbol = item.get("symbol")
            coin_id = item.get("id")
            if symbol in symbols and isinstance(coin_id, int):
                id_map[symbol] = coin_id
        return id_map

    def fetch_ohlcv(
        self,
        coin_id: int,
        symbol: str,
        interval: str,
        time_start: datetime,
        time_end: datetime,
        convert: str = "USD",
    ) -> pd.DataFrame:
        payload = self._request(
            "/v2/cryptocurrency/ohlcv/historical",
            {
                "id": coin_id,
                "interval": interval,
                "time_start": time_start.isoformat(),
                "time_end": time_end.isoformat(),
                "convert": convert,
            },
        )
        return parse_ohlcv_payload(payload, symbol=symbol, interval=interval, convert=convert)

    def fetch_ohlcv_chunked(
        self,
        coin_id: int,
        symbol: str,
        interval: str,
        time_start: datetime,
        time_end: datetime,
        convert: str = "USD",
    ) -> pd.DataFrame:
        """Fetch OHLCV in chunks to avoid per-request data caps."""
        chunk_days = 365 if interval == "daily" else 60
        current_start = time_start
        chunks: list[pd.DataFrame] = []

        while current_start < time_end:
            current_end = min(current_start + timedelta(days=chunk_days), time_end)
            chunk = self.fetch_ohlcv(
                coin_id=coin_id,
                symbol=symbol,
                interval=interval,
                time_start=current_start,
                time_end=current_end,
                convert=convert,
            )
            if not chunk.empty:
                chunks.append(chunk)
            # +1 second avoids requesting same boundary candle repeatedly.
            current_start = current_end + timedelta(seconds=1)

        if not chunks:
            return pd.DataFrame()

        df = pd.concat(chunks, ignore_index=True)
        df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
        return df


def parse_ohlcv_payload(
    payload: dict[str, Any], symbol: str, interval: str, convert: str = "USD"
) -> pd.DataFrame:
    """Normalize CMC OHLCV payload to a tidy dataframe."""
    data = payload.get("data", {})

    # v2 returns a dictionary keyed by coin id.
    if isinstance(data, dict) and data:
        first = next(iter(data.values()))
    else:
        first = data

    quotes = first.get("quotes", []) if isinstance(first, dict) else []
    rows: list[dict[str, Any]] = []
    for quote in quotes:
        quote_ccy = quote.get("quote", {}).get(convert, {})
        rows.append(
            {
                "timestamp": quote.get("time_open"),
                "open": quote_ccy.get("open"),
                "high": quote_ccy.get("high"),
                "low": quote_ccy.get("low"),
                "close": quote_ccy.get("close"),
                "volume": quote_ccy.get("volume"),
                "market_cap": quote_ccy.get("market_cap"),
                "symbol": symbol,
                "pair": SYMBOL_TO_PAIR.get(symbol, f"{symbol.lower()}usdt.p"),
                "interval": interval,
                "source": "coinmarketcap",
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    return df


def save_ohlcv(df: pd.DataFrame, output_dir: Path, symbol: str, interval: str) -> Path:
    """Save OHLCV dataset as parquet file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{symbol.lower()}_{interval}.parquet"
    out_path = output_dir / filename
    df.to_parquet(out_path, index=False)
    return out_path


def last_n_years_window(years: int) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=365 * years)
    return start, end
