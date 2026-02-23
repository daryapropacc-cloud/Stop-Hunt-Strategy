# Historical Crypto Data Review (1H OHLC, Top 50 Coins)

## Goal
Build a reliable pipeline for **1-hour OHLCV** data across the **top 50 coins by market cap**.

---

## What “best” should mean for this use case

For strategy research and backtesting, the best data approach should optimize:

1. **Coverage**: all top 50 symbols available with consistent history.
2. **Data quality**: stable candles, minimal gaps, consistent timestamps.
3. **Operational simplicity**: easy to automate and refresh.
4. **Cost**: free where possible for initial R&D.
5. **Reproducibility**: versioned snapshots and deterministic rebuilds.

---

## Candidate approaches

## 1) Direct exchange REST/Kline endpoints (best free baseline)

Examples: Binance, Bybit, OKX, Coinbase, Kraken.

### Pros
- Free access for historical candles on most exchanges.
- No dependency on third-party aggregators.
- High granularity and native market microstructure per venue.

### Cons
- **Symbol mapping complexity** (e.g., `BTCUSDT` vs `BTC-USD`).
- Data quality varies by exchange and listing lifecycle.
- Must choose quote conventions (`USDT`/`USD`) and handle missing pairs.

### Fit for your use case
Strong option if you want exchange-specific realism (especially for futures/perps backtests).

---

## 2) CCXT-based multi-exchange ingestion (best developer velocity)

CCXT unifies endpoints across many exchanges via one Python interface.

### Pros
- One interface to fetch OHLCV from many venues.
- Faster to implement top-50 coverage than native clients.
- Easy fallback logic when one exchange lacks a pair.

### Cons
- Unified abstraction can hide exchange-specific quirks.
- Rate-limit handling still needed.
- Some endpoints/fields vary by exchange support.

### Fit for your use case
**Best starting choice** for quickly collecting top-50 1H candles while keeping code maintainable.

---

## 3) Market data vendors / aggregators (best data quality, usually paid)

Examples: Kaiko, CoinAPI, CryptoCompare, Coin Metrics, Amberdata.

### Pros
- Cleaner historical datasets and better normalization.
- Better SLAs and less ingestion engineering overhead.
- Often includes richer metadata and corrections.

### Cons
- Paid plans can be expensive.
- Vendor lock-in risk.
- Sometimes delayed data depending on plan.

### Fit for your use case
Best when moving from R&D to production-grade research at scale.

---

## 4) Public market-cap providers for universe selection + exchange OHLC for candles (recommended hybrid)

Use **CoinGecko/CoinMarketCap** only to determine top-50 constituents, then fetch actual 1H candles from exchange APIs (preferably through CCXT).

### Pros
- Clean separation of concerns: 
  - universe selection = market-cap provider
  - candle history = trading venue source
- Avoids relying on index/derived OHLC from listing sites.

### Cons
- Requires two pipelines (universe + candles).

### Fit for your use case
**Most practical architecture** for your project goals.

---

## Recommended stack (Phase 1)

1. **Universe source**: CoinGecko top market-cap list (refresh daily).
2. **Primary OHLC source**: Binance spot/perp via CCXT.
3. **Fallback source**: Bybit/OKX via CCXT when symbol unavailable on Binance.
4. **Storage**: Partitioned Parquet by `exchange/symbol/timeframe/year/month`.
5. **Quality checks**:
   - expected 1H cadence
   - duplicate timestamps
   - gap ratio per symbol
   - stale series detection

This gives the best balance of speed, cost, and backtest reliability.

---

## Implementation details for top-50 + 1H candles

## Universe rules
- Start with top 50 by market cap.
- Exclude stablecoins and wrapped assets unless explicitly needed.
- Map each asset to preferred tradable quote pair (`USDT` first, then `USD`).

## Candle schema
- `timestamp` (UTC, candle open time)
- `open`, `high`, `low`, `close`, `volume`
- `symbol`, `exchange`, `timeframe`
- Optional: `num_trades`, `quote_volume` where available

## Backfill strategy
- Pull in paginated windows until desired start date.
- Re-run idempotently and overwrite conflicting windows.
- Keep raw pull logs to audit gaps and retries.

## Refresh strategy
- Daily incremental job fetching latest candles.
- Reconciliation task to patch missing historical candles weekly.

---

## Key pitfalls to avoid

1. **Mixing candles from different exchanges without tagging venue**.
2. **Timezone inconsistency** (must be UTC end-to-end).
3. **Survivorship bias** (today’s top-50 differs historically).
4. **Ignoring delisted/late-listed assets**.
5. **Not modeling fees/slippage/funding later in backtests**.

---

## Suggested decision for this project now

For immediate progress, use this plan:

- **Top-50 list**: CoinGecko API snapshot each rebalance date.
- **1H OHLCV**: CCXT (`binance` primary, `bybit` fallback).
- **Universe freeze option**: 
  - either fixed top-50 at start date (simple), or
  - rolling monthly top-50 reconstitution (more realistic).

If you want, next I can implement:
1) a `data/universe.py` module for top-50 retrieval,
2) a `data/ohlcv_loader.py` module with CCXT backfill,
3) data quality validation reports per symbol.
