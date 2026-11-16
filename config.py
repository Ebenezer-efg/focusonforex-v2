from __future__ import annotations
from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Risk & limits
    RISK_PER_TRADE_PCT: float = 0.0025
    DAILY_LOSS_LIMIT_PCT: float = 0.01
    DRAWDOWN_LOCK_PCT: float = 0.05
    MIN_RR_RATIO: float = 2.0
    MAX_OPEN_POSITIONS: int = 1
    MAX_CONSECUTIVE_LOSSES: int = 2
    MAX_EFFECTIVE_LEVERAGE: float = 50.0
    MAX_EFFECTIVE_LEVERAGE_NEWS: float = 20.0
    BROKER_UTC_OFFSET_HOURS: int = 2
    CONFLUENCE_FLOOR: int = 65
    ACCOUNT_BALANCE_USD_DEFAULT: float = 1000.0
    SWAP_BUDGET_PCT_OF_RISK: float = 0.25
    DUPLICATE_WINDOW_MINUTES: int = 60

    # Kelly
    KELLY_MIN_TRADES: int = 100
    KELLY_FRACTION: float = 0.25
    KELLY_CAP_PCT: float = 0.0025
    KELLY_FLOOR_PCT: float = 0.0010

    # AI
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    AI_CONSENSUS_CONFIDENCE: int = 70
    AI_TIMEOUT_SECONDS: float = 30.0
    AI_MAX_RETRIES: int = 1

    # Symbols
    BROKER_SYMBOL_MAP: dict[str, str] = {
        "EURUSD": "EURUSDm", "GBPUSD": "GBPUSDm",
        "USDJPY": "USDJPYm", "EURGBP": "EURGBPm",
        "USDCHF": "USDCHFm", "XAUUSD": "XAUUSDm",
    }

    def get_symbol_specs(self) -> dict[str, SymbolSpec]:
        from core.contracts import SymbolSpec
        return {
            "EURUSD": SymbolSpec("EURUSD", self.BROKER_SYMBOL_MAP["EURUSD"], Decimal("0.0001"), Decimal("100000"), Decimal("0.01"), Decimal("50"), Decimal("0.01"), Decimal("2.0"), Decimal("3.0"), Decimal("-7.5"), Decimal("1.5")),
            "GBPUSD": SymbolSpec("GBPUSD", self.BROKER_SYMBOL_MAP["GBPUSD"], Decimal("0.0001"), Decimal("100000"), Decimal("0.01"), Decimal("50"), Decimal("0.01"), Decimal("2.5"), Decimal("3.0"), Decimal("-5.0"), Decimal("-1.0")),
            "USDJPY": SymbolSpec("USDJPY", self.BROKER_SYMBOL_MAP["USDJPY"], Decimal("0.01"), Decimal("100000"), Decimal("0.01"), Decimal("50"), Decimal("0.01"), Decimal("2.0"), Decimal("3.0"), Decimal("2.0"), Decimal("-8.0")),
            "EURGBP": SymbolSpec("EURGBP", self.BROKER_SYMBOL_MAP["EURGBP"], Decimal("0.0001"), Decimal("100000"), Decimal("0.01"), Decimal("50"), Decimal("0.01"), Decimal("2.5"), Decimal("3.0"), Decimal("-3.0"), Decimal("-1.5")),
            "USDCHF": SymbolSpec("USDCHF", self.BROKER_SYMBOL_MAP["USDCHF"], Decimal("0.0001"), Decimal("100000"), Decimal("0.01"), Decimal("50"), Decimal("0.01"), Decimal("2.5"), Decimal("3.0"), Decimal("1.0"), Decimal("-6.0")),
            "XAUUSD": SymbolSpec("XAUUSD", self.BROKER_SYMBOL_MAP["XAUUSD"], Decimal("0.10"), Decimal("100"), Decimal("0.01"), Decimal("20"), Decimal("0.01"), Decimal("50.0"), Decimal("50.0"), Decimal("-47.47"), Decimal("9.0")),
        }
