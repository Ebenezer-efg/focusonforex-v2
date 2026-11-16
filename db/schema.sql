import os
import sys
import logging
import psycopg
from psycopg.rows import dict_row

log = logging.getLogger(__name__)

class AuditUnavailable(Exception):
    pass

def write_audit(action: str, actor: str, payload: dict) -> None:
    """Write to append-only audit_log. Fails closed."""
    db_url = os.getenv("DATABASE_URL_AUDIT", "")
    if not db_url:
        log.error("DATABASE_URL_AUDIT missing! Failing closed.")
        raise AuditUnavailable("Missing audit DB connection string")

    try:
        # Timeout 5s, insert only
        with psycopg.connect(db_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_log (action, actor, payload) VALUES (%s, %s, %s)",
                    (action, actor, psycopg.types.json.Jsonb(payload))
                )
            conn.commit()
    except Exception as e:
        log.error(f"Audit write failed: {e}")
        raise AuditUnavailable("Audit DB unavailable")

# NOTE: tests/test_audit_failclosed.py will be required in Phase 2/7 
# to verify that when this raises, trade submission is blocked.
