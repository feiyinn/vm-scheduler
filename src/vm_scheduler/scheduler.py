from __future__ import annotations

import logging

from vm_scheduler.config import AppConfig
from vm_scheduler.database import is_trade_day
from vm_scheduler.virsh import start_targets, stop_targets

LOGGER = logging.getLogger(__name__)


def execute(action: str, config: AppConfig, dry_run: bool = False) -> int:
    trade_day = is_trade_day(config.database)
    if trade_day is None:
        trade_day = config.policy.assume_trade_day_when_missing
        LOGGER.warning(
            "Trade calendar returned no row. Falling back to assume_trade_day_when_missing=%s.",
            trade_day,
        )

    if not trade_day:
        LOGGER.info("Today is not a trade day. Action '%s' skipped.", action)
        return 0

    if action == "start":
        targets = config.vm_groups.start_targets
    elif action == "stop":
        targets = config.vm_groups.stop_targets
    else:
        raise ValueError(f"Unsupported action: {action}")

    LOGGER.info("Trade day confirmed. Action=%s Targets=%s", action, ", ".join(targets))
    if dry_run:
        LOGGER.info("Dry-run enabled. No virsh command will be executed.")
        return 0

    if action == "start":
        start_targets(config.virsh, targets)
    else:
        stop_targets(config.virsh, targets)
    return 0
