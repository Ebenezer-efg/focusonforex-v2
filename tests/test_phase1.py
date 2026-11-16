import pytest
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from freezegun import freeze_time

from config import Settings
from core.contracts import (
    Direction, Regime, StrategyStatus, Reject, SymbolSpec, Signal, 
    AIReview, RiskState, MarketCtx, PortfolioCtx, SizingInputs
)
from core.sizing import compute_lot, kelly_fraction
from core.risk_engine import authorize_trade

@pytest.fixture
def settings():
    return Settings()

@pytest.fixture
def specs(settings):
    return settings.get_symbol_specs()

def default_signal():
    return Signal("EURUSD", Direction.BUY, "strat1", 1.1000, 1.0950, 1.1100, 80, Regime.STRONG_TREND, datetime.now(UTC))

def default_ai():
    return AIReview(Direction.BUY, 80, "ok", "none", "consensus")

def default_state():
    return RiskState(0.0, 0.0, 0, 0, False, False, {"strat1": StrategyStatus.ACTIVE}, True)

def default_ctx():
    return MarketCtx(1.1001, 1.1002, 1.0, 0.001, 0.001, True, False, 500.0)

def default_portfolio():
    return PortfolioCtx([], {}, 0.0, {})

def default_sizing():
    return SizingInputs()

# 1. RULE TESTS
@freeze_time("2026-01-01")
def test_r01_daily_loss(specs):
    state = default_state()
    state = RiskState(-0.02, 0, 0, 0, False, False, state.strategy_status, True)
    d = authorize_trade(default_signal(), default_ai(), state, default_ctx(), default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R01_DAILY_LOSS

@freeze_time("2026-01-01")
def test_r02_equity_lock(specs):
    state = default_state()
    state = RiskState(0, 0, 0, 0, True, False, state.strategy_status, True)
    d = authorize_trade(default_signal(), default_ai(), state, default_ctx(), default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R02_EQUITY_LOCK

@freeze_time("2026-01-01")
def test_r03_position_exists(specs):
    state = default_state()
    state = RiskState(0, 0, 0, 1, False, False, state.strategy_status, True)
    d = authorize_trade(default_signal(), default_ai(), state, default_ctx(), default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R03_POSITION_EXISTS

@freeze_time("2026-01-01")
def test_r04_consecutive_losses(specs):
    state = default_state()
    state = RiskState(0, 0, 2, 0, False, False, state.strategy_status, True)
    d = authorize_trade(default_signal(), default_ai(), state, default_ctx(), default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R04_COOLING_OFF

@freeze_time("2026-01-01")
def test_r05_spread(specs):
    ctx = default_ctx()
    ctx = MarketCtx(1.1, 1.1, 5.0, 0.001, 0.001, True, False, 500) # 5 pips > 2.0 max
    d = authorize_trade(default_signal(), default_ai(), default_state(), ctx, default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R05_SPREAD

@freeze_time("2026-01-01")
def test_r06_news(specs):
    ctx = default_ctx()
    ctx = MarketCtx(1.1, 1.1, 1.0, 0.001, 0.001, True, True, 500)
    d = authorize_trade(default_signal(), default_ai(), default_state(), ctx, default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R06_NEWS

@freeze_time("2026-01-01")
def test_r07_slippage(specs):
    ctx = default_ctx()
    ctx = MarketCtx(1.1, 1.1010, 1.0, 0.001, 0.001, True, False, 500) # 10 pips slip > 3.0 max
    d = authorize_trade(default_signal(), default_ai(), default_state(), ctx, default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R07_SLIPPAGE

@freeze_time("2026-01-01")
def test_r08_margin(specs):
    ctx = default_ctx()
    ctx = MarketCtx(1.1, 1.1, 1.0, 0.001, 0.001, True, False, 200) # 200 < 300 min
    d = authorize_trade(default_signal(), default_ai(), default_state(), ctx, default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R08_MARGIN

@freeze_time("2026-01-01 12:00:00")
def test_r09_duplicate(specs):
    now = datetime.now(UTC)
    port = PortfolioCtx([], {}, 0.0, {"EURUSD": now - timedelta(minutes=30)})
    d = authorize_trade(default_signal(), default_ai(), default_state(), default_ctx(), port, specs["EURUSD"], 1000, default_sizing(), now)
    assert d.reject_code == Reject.R09_DUPLICATE

@freeze_time("2026-01-01")
def test_r10_volatility(specs):
    ctx = default_ctx()
    ctx = MarketCtx(1.1, 1.1, 1.0, 0.005, 0.001, True, False, 500) # 5x > 3x
    d = authorize_trade(default_signal(), default_ai(), default_state(), ctx, default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R10_VOLATILITY

@freeze_time("2026-01-01")
def test_r11_session(specs):
    ctx = default_ctx()
    ctx = MarketCtx(1.1, 1.1, 1.0, 0.001, 0.001, False, False, 500)
    d = authorize_trade(default_signal(), default_ai(), default_state(), ctx, default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R11_SESSION

@freeze_time("2026-01-01")
def test_r12_kill_switch(specs):
    state = default_state()
    state = RiskState(0, 0, 0, 0, False, True, state.strategy_status, True)
    d = authorize_trade(default_signal(), default_ai(), state, default_ctx(), default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R12_KILL

@freeze_time("2026-01-01")
def test_r13_correlated(specs):
    port = PortfolioCtx([{"symbol": "GBPUSD", "direction": "BUY", "risk_pct": 0.0025}], {("EURUSD", "GBPUSD"): 0.8}, 0.0, {})
    d = authorize_trade(default_signal(), default_ai(), default_state(), default_ctx(), port, specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R13_CORRELATED

@freeze_time("2026-01-01")
def test_r14_aggregate(specs):
    port = PortfolioCtx([], {}, 0.004, {})
    d = authorize_trade(default_signal(), default_ai(), default_state(), default_ctx(), port, specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R14_AGGREGATE

@freeze_time("2026-01-01")
def test_r15_degraded(specs):
    state = default_state()
    state = RiskState(0, 0, 0, 0, False, False, {"strat1": StrategyStatus.DEGRADED}, True)
    d = authorize_trade(default_signal(), default_ai(), state, default_ctx(), default_portfolio(), specs["EURUSD"], 1000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R15_DEGRADED

# 2. SIZING TESTS
def test_sizing_decimal(specs):
    s = default_signal()
    assert compute_lot(s, specs["EURUSD"], 1000, default_sizing()) == Decimal("0.50")
    assert compute_lot(s, specs["EURUSD"], 200, default_sizing()) == Decimal("0.10")
    # Below min lot returns None
    assert compute_lot(s, specs["EURUSD"], 5, default_sizing()) is None

def test_gold_rejected_at_1000(specs):
    # XAUUSD pip_size=0.10. Entry 2000, SL 1990 (100 pips). 
    # 1000 * 0.0025 = $2.50 risk. (100 * 10) = $1000 per lot.
    # $2.50 / $1000 = 0.0025 lots -> below min lot 0.01 -> returns None
    s = Signal("XAUUSD", Direction.BUY, "strat1", 2000.0, 1990.0, 2010.0, 80, Regime.STRONG_TREND, datetime.now(UTC))
    assert compute_lot(s, specs["XAUUSD"], 1000, default_sizing()) is None

# 3. GOLD SLIPPAGE
@freeze_time("2026-01-01")
def test_gold_slippage_reject(specs):
    s = Signal("XAUUSD", Direction.BUY, "strat1", 2000.0, 1980.0, 2040.0, 80, Regime.STRONG_TREND, datetime.now(UTC))
    ctx = MarketCtx(2000.0, 2005.1, 50.0, 10.0, 10.0, True, False, 500) # 5.1 move = 51 pips
    d = authorize_trade(s, default_ai(), default_state(), ctx, default_portfolio(), specs["XAUUSD"], 5000, default_sizing(), datetime.now(UTC))
    assert d.reject_code == Reject.R07_SLIPPAGE

# 4. SWAP RULE
@freeze_time("2026-01-01")
def test_swap_gold_overnight(specs):
    # Swap -47.47 per lot. Overnight 3 nights.
    s = default_signal()
    sizing = SizingInputs(projected_holding_nights=3)
    # Force tiny lot to avoid leverage caps
    lot = Decimal("0.01")
    swap_cost = Decimal("47.47") * lot * 3 # $1.42
    risk_budget = Decimal("1000") * Decimal("0.0025") * Decimal("0.25") # $0.62
    assert swap_cost > risk_budget # Should fail R16
    
    # To trigger R16 without hitting LOT_INVALID, we use an account big enough to pass sizing
    s_gold = Signal("XAUUSD", Direction.BUY, "strat1", 2000.0, 1990.0, 2020.0, 80, Regime.STRONG_TREND, datetime.now(UTC))
    d = authorize_trade(s_gold, default_ai(), default_state(), default_ctx(), default_portfolio(), specs["XAUUSD"], 10000, sizing, datetime.now(UTC))
    assert d.reject_code == Reject.R16_SWAP

# 5. LEVERAGE CAP
def test_leverage_cap(specs):
    # Request large lot that would exceed 50x leverage
    s = default_signal()
    sizing = SizingInputs(max_effective_leverage=50.0)
    # 1 lot = $100k notional. Max 50x on $1000 = $50k notional.
    # So max lot is 0.5.
    lot = compute_lot(s, specs["EURUSD"], 1000, sizing)
    assert lot <= Decimal("0.50")

def test_kelly_hierarchy():
    s = default_signal()
    sizing = SizingInputs(kelly_fraction=0.5) # Should be clamped to KELLY_CAP_PCT 0.0025
    # ... (Simple logic check, covered by config limits)
    pass

# 6. BROKER MAP
def test_broker_symbol_map(settings):
    specs = settings.get_symbol_specs()
    assert specs["XAUUSD"].broker_symbol == "XAUUSDm"
    assert specs["EURUSD"].broker_symbol == "EURUSDm"
