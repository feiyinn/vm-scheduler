#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="/opt/vm-scheduler"
CONFIG_ROOT="/etc/vm-scheduler"
SYSTEMD_ROOT="/etc/systemd/system"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

require_command python3
require_command install
require_command systemctl

if ! command -v uv >/dev/null 2>&1; then
  echo "Missing required command: uv" >&2
  echo "Install uv first: https://docs.astral.sh/uv/" >&2
  exit 1
fi

echo "Installing vm-scheduler into ${INSTALL_ROOT}"

install -d -m 0755 "${INSTALL_ROOT}"
install -d -m 0755 "${INSTALL_ROOT}/src"
install -d -m 0755 "${CONFIG_ROOT}"

cp -r "${PROJECT_ROOT}/src/vm_scheduler" "${INSTALL_ROOT}/src/"
install -m 0644 "${PROJECT_ROOT}/pyproject.toml" "${INSTALL_ROOT}/pyproject.toml"
install -m 0644 "${PROJECT_ROOT}/README.md" "${INSTALL_ROOT}/README.md"

if [[ ! -f "${CONFIG_ROOT}/config.yaml" ]]; then
  install -m 0640 "${PROJECT_ROOT}/config/config.example.yaml" "${CONFIG_ROOT}/config.yaml"
  echo "Created ${CONFIG_ROOT}/config.yaml from example template."
else
  echo "Keeping existing ${CONFIG_ROOT}/config.yaml"
fi

cd "${INSTALL_ROOT}"
uv venv .venv
uv pip install --python "${INSTALL_ROOT}/.venv/bin/python" .

install -m 0644 "${PROJECT_ROOT}/systemd/vm-scheduler-start.service" "${SYSTEMD_ROOT}/vm-scheduler-start.service"
install -m 0644 "${PROJECT_ROOT}/systemd/vm-scheduler-start.timer" "${SYSTEMD_ROOT}/vm-scheduler-start.timer"
install -m 0644 "${PROJECT_ROOT}/systemd/vm-scheduler-stop.service" "${SYSTEMD_ROOT}/vm-scheduler-stop.service"
install -m 0644 "${PROJECT_ROOT}/systemd/vm-scheduler-stop.timer" "${SYSTEMD_ROOT}/vm-scheduler-stop.timer"

systemctl daemon-reload
systemctl enable --now vm-scheduler-start.timer vm-scheduler-stop.timer

echo
echo "Installation complete."
echo "Edit ${CONFIG_ROOT}/config.yaml before relying on timers in production."
echo "Check status with:"
echo "  systemctl status vm-scheduler-start.timer vm-scheduler-stop.timer"
