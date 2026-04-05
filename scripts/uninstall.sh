#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="/opt/vm-scheduler"
CONFIG_ROOT="/etc/vm-scheduler"
SYSTEMD_ROOT="/etc/systemd/system"

systemctl disable --now vm-scheduler-start.timer vm-scheduler-stop.timer 2>/dev/null || true
systemctl disable --now vm-scheduler-start.service vm-scheduler-stop.service 2>/dev/null || true

rm -f "${SYSTEMD_ROOT}/vm-scheduler-start.service"
rm -f "${SYSTEMD_ROOT}/vm-scheduler-start.timer"
rm -f "${SYSTEMD_ROOT}/vm-scheduler-stop.service"
rm -f "${SYSTEMD_ROOT}/vm-scheduler-stop.timer"

systemctl daemon-reload

rm -rf "${INSTALL_ROOT}"
rm -rf "${CONFIG_ROOT}"

echo "vm-scheduler removed."
