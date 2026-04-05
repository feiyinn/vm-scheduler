from __future__ import annotations

from datetime import date
from typing import Any

import psycopg

from vm_scheduler.config import DatabaseConfig


TRUE_VALUES = {"1", "true", "t", "y", "yes"}
FALSE_VALUES = {"0", "false", "f", "n", "no"}


def normalize_trade_day_value(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)

    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    raise ValueError(f"Unsupported trade-day result value: {value!r}")


def is_trade_day(db_config: DatabaseConfig, today: date | None = None) -> bool | None:
    actual_day = today or date.today()
    params = {"today": actual_day.isoformat()}

    with psycopg.connect(db_config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(db_config.trade_day_sql, params)
            row = cur.fetchone()

    if row is None:
        return None

    return normalize_trade_day_value(row[0])
