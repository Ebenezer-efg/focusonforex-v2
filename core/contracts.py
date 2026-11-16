
```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Regime(str, Enum):
    STRONG_TREND = "STRONG_TREND"
    WEAK_TREND = "WEAK_TREND"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"


class StrategyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"


class Reject(str, Enum):
    R01_DAILY_LOSS = "R01_DAILY_LOSS"
    R02_EQUITY_LOCK = "R02_EQUITY_LOCK"
    R03_POSITION_EXISTS = "R03_POSITION_EXISTS"
    R04_COOLING_OFF = "R04_COOLING_OFF"
    R05_SPREAD = "R05_SPREAD"
    R06_NEWS = "R06_NEWS"
    R07_SLIPPAGE = "R07_SLIPPAGE"
    R08_MARGIN = "R08_MARGIN"
    R09_DUPLICATE = "R09_DUPLICATE"
    R10_VOLATILITY = "R10_VOLATILITY"
    R11_SESSION = "R11_SESSION"
    R12_KILL = "R12_KILL"
    R13_CORRELATED = "R13_CORRELATED"
    R14_AGGREGATE = "R14_AGGREGATE"
    R15_DEGRADED = "R15_DEGRADED"
    R16_SWAP = "R16_SWAP"
    LOT_INVALID = "LOT_INVALID"


@dataclass(frozen=True)
class SymbolSpec:
    symbol: str
    broker_symbol: str
    pip_size: Decimal
    contract_size: Decimal
    volume_min: Decimal
    volume_max: Decimal
    volume_step: Decimal
    max_spread_pips: Decimal
    max_slippage_pips: Decimal
    swap_long_per_lot_night: Decimal
    swap_short_per_lot_night: Decimal


@dataclass(frozen=True)
class Signal:
    symbol: str
    direction: Direction
    strategy: str
    entry: float
    sl: float
    tp: float
    confluence: int
    regime: Regime
    created_at: datetime


@dataclass(frozen=True)
class AIReview:
    signal: Direction | None
    confidence: int
    reasoning: str
    key_risk: str
    source: str


@dataclass(frozen=True)
class RiskState:
    daily_pnl_pct: float
    drawdown_pct: float
    consecutive_losses: int
    open_positions: int
    equity_lock: bool
    kill_switch: bool
    strategy_status: dict[str, StrategyStatus]
    approval_valid: bool


@dataclass(frozen=True)
class MarketCtx:
    live_bid: float
    live_ask: float
    spread_pips: float
    atr_current: float
    atr_avg_20: float
    session_active: bool
    news_blocked: bool
    margin_level_post_entry_pct: float


@dataclass(frozen=True)
class PortfolioCtx:
    open_positions: list[dict]
    correlation_matrix: dict[tuple[str, str], float]
    aggregate_open_risk_pct: float
    last_order_at_by_symbol: dict[str, datetime]


@dataclass(frozen=True)
class SizingInputs:
    crowding_penalty: float = 1.0
    kelly_fraction: float | None = None
    projected_holding_nights: int = 1
    max_effective_leverage: float = 50.0


@dataclass(frozen=True)
class Decision:
    approved: bool
    lot_size: Decimal | None
    reject_code: Reject | None
    reason: str
```
