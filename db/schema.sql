-- Run this file via direct Postgres connection (psql or Supabase SQL Editor) as the `postgres` owner.
-- App runtime uses TWO connections:
--   1) supabase-py (PostgREST) for all tables EXCEPT audit_log
--   2) direct psycopg connection as `audit_writer` for audit_log only
-- If audit_writer connection fails, FAIL CLOSED: log to stderr and refuse to trade.

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  payload JSONB,
  ip TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE ROLE IF NOT EXISTS audit_writer NOLOGIN;
GRANT USAGE ON SCHEMA public TO audit_writer;
GRANT INSERT ON audit_log TO audit_writer;
GRANT USAGE ON SEQUENCE audit_log_id_seq TO audit_writer;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM audit_writer;

CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_log is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_log_immutable ON audit_log;
CREATE TRIGGER audit_log_immutable
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

CREATE TABLE IF NOT EXISTS risk_state (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  daily_pnl_pct NUMERIC(6,4) DEFAULT 0,
  drawdown_pct NUMERIC(6,4) DEFAULT 0,
  consecutive_losses INT DEFAULT 0,
  equity_lock BOOLEAN DEFAULT FALSE NOT NULL,
  lock_at TIMESTAMPTZ,
  cooling_off_until TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id BIGINT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED','EXPIRED','PENDING_OFFLINE','EXPIRED_OFFLINE')),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  decided_at TIMESTAMPTZ,
  telegram_msg_id BIGINT
);

CREATE TABLE IF NOT EXISTS strategy_state (
  strategy TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','DEGRADED','RETIRED')),
  parameter_lock BOOLEAN DEFAULT FALSE NOT NULL,
  last_wfa_pass TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Remaining placeholder tables (you will fill these in Phase 2+)
CREATE TABLE IF NOT EXISTS accounts (id BIGSERIAL PRIMARY KEY, broker TEXT, balance NUMERIC);
CREATE TABLE IF NOT EXISTS signals (id BIGSERIAL PRIMARY KEY, symbol TEXT, strategy TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS ai_reviews (id BIGSERIAL PRIMARY KEY, symbol TEXT, strategy TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS orders (id BIGSERIAL PRIMARY KEY, symbol TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS positions (id BIGSERIAL PRIMARY KEY, symbol TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS trade_history (id BIGSERIAL PRIMARY KEY, symbol TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS risk_events (id BIGSERIAL PRIMARY KEY, rule_code TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS kill_switch (id BIGSERIAL PRIMARY KEY, active BOOLEAN DEFAULT FALSE);

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategy_state ENABLE ROW LEVEL SECURITY;
