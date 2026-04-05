from __future__ import annotations

import logging
import subprocess

from vm_scheduler.config import VirshConfig

LOGGER = logging.getLogger(__name__)


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    LOGGER.info("Executing: %s", " ".join(command))
    return subprocess.run(command, check=True, text=True, capture_output=True)


def list_running_vms(binary: str) -> set[str]:
    result = _run_command([binary, "list", "--name"])
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def start_vm(config: VirshConfig, vm_name: str) -> None:
    _run_command([config.binary, config.start_mode, vm_name])


def shutdown_vm(config: VirshConfig, vm_name: str) -> None:
    _run_command([config.binary, config.shutdown_mode, vm_name])


def stop_targets(config: VirshConfig, vm_names: list[str]) -> None:
    running = list_running_vms(config.binary)
    for vm_name in vm_names:
        if vm_name not in running:
            LOGGER.info("VM '%s' is already stopped; skipping.", vm_name)
            continue
        shutdown_vm(config, vm_name)


def start_targets(config: VirshConfig, vm_names: list[str]) -> None:
    running = list_running_vms(config.binary)
    for vm_name in vm_names:
        if vm_name in running:
            LOGGER.info("VM '%s' is already running; skipping.", vm_name)
            continue
        start_vm(config, vm_name)
