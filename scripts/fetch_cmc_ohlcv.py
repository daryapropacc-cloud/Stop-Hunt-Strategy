#!/usr/bin/env python3
"""Fetch Daily + 1H OHLCV for selected crypto symbols from CoinMarketCap."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from stop_hunt_strategy.data.cmc_ohlcv import CmcOhlcvClient, last_n_years_window, save_ohlcv

TARGET_SYMBOLS = ["BTC", "ETH", "SOL", "XRP", "DOGE"]
TARGET_INTERVALS = ["daily", "hourly"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", default=os.getenv("CMC_API_KEY"), help="CoinMarketCap API key")
    parser.add_argument("--years", type=int, default=3, help="How many years back to fetch")
    parser.add_argument(
        "--output-dir", default="data/raw/cmc", help="Directory to store parquet output files"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise ValueError("Missing API key. Pass --api-key or set CMC_API_KEY.")

    client = CmcOhlcvClient(api_key=args.api_key)
    start, end = last_n_years_window(args.years)
    id_map = client.get_id_map(TARGET_SYMBOLS)

    output_dir = Path(args.output_dir)
    for symbol in TARGET_SYMBOLS:
        if symbol not in id_map:
            print(f"[WARN] {symbol}: no CMC id found, skipping")
            continue

        coin_id = id_map[symbol]
        for interval in TARGET_INTERVALS:
            try:
                df = client.fetch_ohlcv_chunked(
                    coin_id=coin_id,
                    symbol=symbol,
                    interval=interval,
                    time_start=start,
                    time_end=end,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[ERROR] {symbol} {interval}: {exc}")
                continue

            if df.empty:
                print(f"[WARN] {symbol} {interval}: no rows returned")
                continue

            out_path = save_ohlcv(df, output_dir=output_dir, symbol=symbol, interval=interval)
            print(f"[OK] {symbol} {interval}: {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
