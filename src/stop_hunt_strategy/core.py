"""Core interfaces for the strategy research framework."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import pandas as pd


@dataclass(slots=True)
class Signal:
    """Trading intent emitted by a strategy."""

    timestamp: datetime
    symbol: str
    side: str  # "long" | "short" | "flat"
    strength: float


class DataProvider(Protocol):
    def load_ohlcv(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Return OHLCV indexed by timestamp."""


class FeaturePipeline(Protocol):
    def transform(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Return feature dataframe aligned to market_data index."""


class Strategy(Protocol):
    def generate_signals(self, features: pd.DataFrame) -> pd.DataFrame:
        """Return signals indexed by timestamp."""


class RiskManager(Protocol):
    def adjust_position_size(self, signal: Signal, equity: float) -> float:
        """Return approved position notional/units."""


class BacktestEngine(Protocol):
    def run(self, market_data: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
        """Return trade log and/or equity curve as dataframe."""


class ReportBuilder(Protocol):
    def build(self, equity_curve: pd.DataFrame, trades: pd.DataFrame) -> dict:
        """Return summary metrics and report artifacts metadata."""
