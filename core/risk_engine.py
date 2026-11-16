"""Deterministic risk engine (R01–R16).

Pure logic. No network. No AI. No broker. No clock.
`now` is injected for R09. Import only from core.contracts, core.sizing, config.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from config import Settings
from core.contracts import (
    AIReview,
    Decision,
    MarketCtx,
    PortfolioCtx,
    Reject,
    RiskState,
    Signal,
    SizingInputs,
    StrategyStatus,
    SymbolSpec,
    Direction,
)
from core.sizing import compute_lot


def authorize_trade(
    signal: Signal,
    ai: AIReview,
    state: RiskState,
    ctx: MarketCtx,
    portfolio: PortfolioCtx,
    spec: SymbolSpec,
    balance: float,
    sizing: SizingInputs,
    now: datetime,
) -> Decision:
    settings = Settings()

    # STEP 0: Compute lot FIRST
    lot = compute_lot(signal, spec, balance, sizing)
    if lot is None:
        return Decision(False, None, Reject.LOT_INVALID, "Lot below broker minimum after sizing / leverage cap")

    # R01: Daily loss
    if state.daily_pnl_pct <= -settings.DAILY_LOSS_LIMIT_PCT:
        return Decision(False, None, Reject.R01_DAILY_LOSS, "Daily loss limit reached")

    # R02: Drawdown / equity lock
    if state.drawdown_pct >= settings.DRAWDOWN_LOCK_PCT or state.equity_lock:
        return Decision(False, None, Reject.R02_EQUITY_LOCK, "Equity lock active or drawdown limit reached")

    # R03: Max open positions
    if state.open_positions >= settings.MAX_OPEN_POSITIONS:
        return Decision(False, None, Reject.R03_POSITION_EXISTS, "Max open positions reached")

    # R04: Consecutive losses
    if state.consecutive_losses >= settings.MAX_CONSECUTIVE_LOSSES:
        return Decision(False, None, Reject.R04_COOLING_OFF, "Consecutive losses limit reached")

    # R05: Spread
    if ctx.spread_pips > float(spec.max_spread_pips):
        return Decision(False, None, Reject.R05_SPREAD, "Spread exceeds maximum")

    # R06: News window
    if ctx.news_blocked:
        return Decision(False, None, Reject.R06_NEWS, "News protection window active")

    # R07: Slippage
    slippage_pips = abs(ctx.live_ask - signal.entry) / float(spec.pip_size)
    if slippage_pips > float(spec.max_slippage_pips):
        return Decision(False, None, Reject.R07_SLIPPAGE, "Slippage exceeds maximum")

    # R08: Margin level
    if ctx.margin_level_post_entry_pct < 300:
        return Decision(False, None, Reject.R08_MARGIN, "Post-entry margin level below 300%")

    # R09: Duplicate window
    last = portfolio.last_order_at_by_symbol.get(signal.symbol)
    if last is not None:
        time_since_last = (now - last).total_seconds()
        if time_since_last < settings.DUPLICATE_WINDOW_MINUTES * 60:
            return Decision(False, None, Reject.R09_DUPLICATE, "Duplicate order within window")

    # R10: Volatility
    if ctx.atr_current > 3 * ctx.atr_avg_20:
        return Decision(False, None, Reject.R10_VOLATILITY, "Abnormal volatility")

    # R11: Session
    if not ctx.session_active:
        return Decision(False, None, Reject.R11_SESSION, "Session inactive")

    # R12: Kill switch / Approval
    if state.kill_switch or not state.approval_valid:
        return Decision(False, None, Reject.R12_KILL, "Kill switch active or approval invalid")

    # R13: Correlation
    usd_side_map = {"EURUSD": -1, "GBPUSD": -1, "USDJPY": 1, "EURGBP": 0, "USDCHF": 1, "XAUUSD": -1}
    new_usd_side = usd_side_map.get(signal.symbol, 0)
    if signal.direction == Direction.SELL:
        new_usd_side *= -1

    if new_usd_side != 0:
        for pos in portfolio.open_positions:
            pos_side = usd_side_map.get(pos["symbol"], 0)
            if pos["direction"] == "SELL":
                pos_side *= -1
            if pos_side == new_usd_side:
                corr = portfolio.correlation_matrix.get((signal.symbol, pos["symbol"]), 0.0)
                if abs(corr) > 0.65:
                    return Decision(False, None, Reject.R13_CORRELATED, "Correlated exposure limit reached")

    # R14: Aggregate risk
    if portfolio.aggregate_open_risk_pct + settings.RISK_PER_TRADE_PCT > 0.005:
        return Decision(False, None, Reject.R14_AGGREGATE, "Aggregate risk limit reached")

    # R15: Strategy degraded
    if state.strategy_status.get(signal.strategy) != StrategyStatus.ACTIVE:
        return Decision(False, None, Reject.R15_DEGRADED, "Strategy is degraded")

    # R16: Swap budget
    swap_per_night = spec.swap_long_per_lot_night if signal.direction == Direction.BUY else spec.swap_short_per_lot_night
    swap_cost_per_lot = max(Decimal("0"), -swap_per_night)
    swap_cost_usd = swap_cost_per_lot * lot * Decimal(sizing.projected_holding_nights)
    risk_budget_usd = Decimal(str(balance)) * Decimal(str(settings.RISK_PER_TRADE_PCT)) * Decimal(str(settings.SWAP_BUDGET_PCT_OF_RISK))
    
    if swap_cost_usd > risk_budget_usd:
        return Decision(False, None, Reject.R16_SWAP, "Swap cost exceeds budget")

    return Decision(True, lot, None, "APPROVED")
