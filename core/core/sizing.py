"""Lot sizing calculation. Decimal only — NEVER float for lot arithmetic.

Option B design: if the computed lot falls below volume_min
(common for XAUUSD on sub-$1200 accounts), return None so the
risk engine rejects with LOT_INVALID. The bot does not increase
risk_per_trade to accommodate minimum lot — it refuses the trade.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR

from config import Settings
from core.contracts import Signal, SizingInputs, SymbolSpec


def compute_lot(
    signal: Signal,
    spec: SymbolSpec,
    balance: float,
    sizing: SizingInputs,
) -> Decimal | None:
    """Calculate lot size. Returns None if below broker minimum."""
    settings = Settings()

    # 1. Base risk percentage
    risk_pct = settings.RISK_PER_TRADE_PCT
    if sizing.kelly_fraction is not None:
        kelly_target = sizing.kelly_fraction * settings.KELLY_FRACTION
        risk_pct = max(settings.KELLY_FLOOR_PCT, min(settings.KELLY_CAP_PCT, kelly_target))

    risk_amount_usd = Decimal(str(balance)) * Decimal(str(risk_pct))

    # 2. Apply crowding penalty (clamped between 0.5 and 1.0)
    penalty = max(0.5, min(1.0, sizing.crowding_penalty))
    risk_amount_usd *= Decimal(str(penalty))

    # 3. Calculate pips at risk
    entry = Decimal(str(signal.entry))
    sl = Decimal(str(signal.sl))
    pips_at_risk = abs(entry - sl) / spec.pip_size
    
    if pips_at_risk == 0:
        return None  # Prevent division by zero if entry == sl

    pip_value_usd = spec.contract_size * spec.pip_size
    raw_lot = risk_amount_usd / (pips_at_risk * pip_value_usd)

    # 4. Snap DOWN to volume_step
    lots_on_step = (raw_lot / spec.volume_step).to_integral_value(rounding=ROUND_FLOOR)
    lot = lots_on_step * spec.volume_step

    # 5. Enforce leverage cap
    notional_usd = lot * spec.contract_size * entry
    leverage = notional_usd / Decimal(str(balance)) if balance > 0 else Decimal("Infinity")

    if leverage > Decimal(str(sizing.max_effective_leverage)):
        max_notional = Decimal(str(balance)) * Decimal(str(sizing.max_effective_leverage))
        lot = max_notional / (spec.contract_size * entry)
        lot = (lot / spec.volume_step).to_integral_value(rounding=ROUND_FLOOR) * spec.volume_step

    # 6. Clamp to broker max/min
    lot = min(lot, spec.volume_max)
    if lot < spec.volume_min:
        return None

    return lot


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate the Kelly Criterion fraction."""
    if avg_loss <= 0 or avg_win <= 0:
        return 0.0
    b = avg_win / avg_loss
    return win_rate - (1 - win_rate) / b
