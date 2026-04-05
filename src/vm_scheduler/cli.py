from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from vm_scheduler.config import DEFAULT_CONFIG_PATH, load_config
from vm_scheduler.logging_utils import configure_logging
from vm_scheduler.scheduler import execute


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vm-scheduler",
        description="Schedule libvirt VMs with trading-day checks.",
    )
    parser.add_argument(
        "action",
        choices=["start", "stop"],
        help="Which VM action to run.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to config YAML.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log the intended action without running virsh.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        configure_logging(config.logging.level)
        return execute(args.action, config, dry_run=args.dry_run)
    except Exception as exc:
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s %(levelname)s %(message)s")
        logging.exception("vm-scheduler failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
