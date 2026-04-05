from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/vm-scheduler/config.yaml")


@dataclass(slots=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    schema: str
    trade_day_sql: str

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"user={self.user} "
            f"password={self.password} "
            f"dbname={self.database}"
        )


@dataclass(slots=True)
class VMGroupsConfig:
    start_targets: list[str]
    stop_targets: list[str]


@dataclass(slots=True)
class VirshConfig:
    binary: str
    shutdown_mode: str
    start_mode: str
    timeout_seconds: int
    poll_interval_seconds: int


@dataclass(slots=True)
class LoggingConfig:
    level: str


@dataclass(slots=True)
class PolicyConfig:
    assume_trade_day_when_missing: bool


@dataclass(slots=True)
class AppConfig:
    database: DatabaseConfig
    vm_groups: VMGroupsConfig
    virsh: VirshConfig
    logging: LoggingConfig
    policy: PolicyConfig


def _require_section(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid '{key}' section in config.")
    return value


def _require_list(raw: dict[str, Any], key: str) -> list[str]:
    value = raw.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Missing or invalid list '{key}' in config.")
    return value


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    database = _require_section(raw, "database")
    vm_groups = _require_section(raw, "vm_groups")
    virsh = _require_section(raw, "virsh")
    logging = _require_section(raw, "logging")
    policy = _require_section(raw, "policy")

    return AppConfig(
        database=DatabaseConfig(
            host=str(database["host"]),
            port=int(database["port"]),
            user=str(database["user"]),
            password=str(database["password"]),
            database=str(database["database"]),
            schema=str(database.get("schema", "public")),
            trade_day_sql=str(database["trade_day_sql"]).strip(),
        ),
        vm_groups=VMGroupsConfig(
            start_targets=_require_list(vm_groups, "start_targets"),
            stop_targets=_require_list(vm_groups, "stop_targets"),
        ),
        virsh=VirshConfig(
            binary=str(virsh.get("binary", "/usr/bin/virsh")),
            shutdown_mode=str(virsh.get("shutdown_mode", "shutdown")),
            start_mode=str(virsh.get("start_mode", "start")),
            timeout_seconds=int(virsh.get("timeout_seconds", 120)),
            poll_interval_seconds=int(virsh.get("poll_interval_seconds", 5)),
        ),
        logging=LoggingConfig(
            level=str(logging.get("level", "INFO")),
        ),
        policy=PolicyConfig(
            assume_trade_day_when_missing=bool(policy.get("assume_trade_day_when_missing", False)),
        ),
    )
