# Trading Strategy Platform Architecture (Crypto-First)

This repository is structured to let us move from idea → research → backtest → analysis quickly and safely.

## 1) High-level workflow

1. **Data Ingestion** (`data/`)
   - Fetch OHLCV + funding/open-interest/liquidation data (where available)
   - Normalize symbols/timezones and persist in a local format (Parquet)
2. **Feature Engineering** (`features/`)
   - Generate indicators, market structure labels, volatility regimes, session windows
3. **Signal / Strategy Logic** (`strategies/`)
   - Convert features into directional entries/exits
4. **Backtesting Engine** (`backtest/`)
   - Event-driven simulation with realistic fees/slippage/funding assumptions
5. **Risk & Position Sizing** (`risk/`)
   - Cap risk per trade/day, set sizing, stop-loss/TP policy
6. **Execution Model** (`execution/`)
   - Paper/live adapters kept separate from strategy core
7. **Analytics & Reporting** (`reporting/`)
   - Performance metrics, regime attribution, and equity-curve diagnostics

---

## 2) Package layout

```text
src/stop_hunt_strategy/
  data/         # market data connectors, schema normalization, storage
  features/     # indicator + market structure feature pipeline
  strategies/   # strategy interface and concrete implementations
  backtest/     # simulator, fills, accounting, portfolio state
  risk/         # sizing rules, drawdown controls, exposure caps
  execution/    # broker/exchange adapters (paper/live later)
  reporting/    # metrics, tearsheets, charts
  utils/        # shared helpers (time, logging, validation)
```

## 3) Design principles

- **Separation of concerns**: strategy logic must not depend on exchange APIs.
- **Deterministic backtests**: same config + same data = same result.
- **Config-driven experiments**: strategy/backtest parameters live in `configs/`.
- **Reproducibility**: store data snapshots and experiment metadata.
- **Extensibility**: easy to swap data source, slippage model, or strategy class.

## 4) Core interfaces (first version)

- `DataProvider`: load candles and optional derivatives data for symbol/timeframe
- `FeaturePipeline`: transform raw market data into model-ready features
- `Strategy`: produce `Signal` objects from features
- `BacktestEngine`: execute signals into trades using execution assumptions
- `RiskManager`: validate/adjust intended position size before order placement
- `ReportBuilder`: compute and export metrics + charts

## 5) Metrics to prioritize

- Net return, CAGR
- Max drawdown
- Sharpe, Sortino
- Win rate, profit factor
- Expectancy per trade
- Average R multiple
- Exposure / time in market
- Fee + slippage impact decomposition

## 6) Recommended development sequence

1. Build and validate data pipeline for 1 exchange + 3 symbols
2. Implement baseline strategy interface and one dummy strategy
3. Build minimal backtest loop with fees/slippage
4. Add performance report with key risk metrics
5. Plug in your stop-hunt strategy rules once you share them

## 7) What we should decide before implementation

- Preferred exchange data source (Binance, Bybit, OKX, etc.)
- Timeframes to support first (e.g., 1m/5m/15m)
- Universe (BTC/ETH only vs wider basket)
- Spot vs futures/perpetuals
- Funding-rate modeling needs (if perp)
- Default fee/slippage assumptions
