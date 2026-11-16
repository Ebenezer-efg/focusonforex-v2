  ```markdown
   # FocusOnForex V2 — Project Context
   
   ## What this is
   Personal AI-assisted Forex/Gold trading bot for a Ghanaian trader (Accra).
   Runs as ONE async Python process. No n8n. No cloud orchestrator.
   Broker: Exness MT5 via MetaApi. DB: Supabase. Interface: Telegram.
   
   ## Hard rules (never violate)
   1. `core/` may NOT import from `ai/`, `execution/`, `interface/`, `ghana/`, `data/`, or any HTTP library.
   2. `core/risk_engine.py` is pure logic: no network, no AI, no broker, no clock.
   3. No trade without explicit Telegram ✅. Offline → expires. Never auto-approve.
   4. No trade unless all 16 risk rules pass. AI confidence never overrides.
   5. `equity_lock` persists in Supabase across restarts.
   6. All times UTC internally. Accra = UTC+0, no DST.
   7. Every scheduled job wrapped in `@resilient`.
   8. Tests come first for `core/`. Never write execution code before risk tests pass.
   
   ## Correctness invariants
   - No `asyncio.gather` for AI calls. Use TaskGroup with per-task error boundaries.
   - No `create_task` without retained handle inside main TaskGroup.
   - No `datetime.now()` inside core/. `now` is injected.
   - No `// 0.01` float arithmetic. Decimal only, snapped to volume_step.
   - No hardcoded pip_size. Always SymbolSpec.
   - Broker server time normalised to UTC at ingestion; offset verified at startup.
   - Only closed bars enter the strategy engine.
   - No `time.sleep` in async code. Enforced by pre-commit grep.
   - PTB Application built manually; never `run_polling()` inside asyncio.run().
   
   ## Autonomy invariants
   - RiskState read fresh at decision time; no cache between DB and gatekeeper.
   - equity_guard is the ONLY writer of equity_lock.
   - Circuit breakers gate new entries only. Exits never gated.
   - Drift DEGRADED permits WFA runs, blocks live trades, never auto-recalibrates.
   - Strategy state: ACTIVE → DEGRADED → (WFA pass→ACTIVE | fail→RETIRED).
   - Kelly enabled only per (strategy, regime) bucket with ≥100 trades + positive expectancy.
   - Crowding penalty clamped [0.5, 1.0]; applied inside lot sizing.
   
   ## Tech stack (pinned)
   Python 3.11+, asyncio, APScheduler (AsyncIOScheduler), python-telegram-bot v21, supabase-py, httpx + tenacity, pydantic v2, structlog, pytest + pytest-asyncio.
   
   ## Style
   - Type hints everywhere.
   - Dataclasses or pydantic models for all inputs/outputs.
   - No global mutable state except via db/.
   - All external calls: timeout + retry + typed failure.
   - Log structured JSON. Never log secrets.
   ```
