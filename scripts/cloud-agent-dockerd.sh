#!/usr/bin/env bash
# Start Docker daemon when it is not already running (nested Cloud Agent VMs).
set -euo pipefail

if docker info >/dev/null 2>&1; then
  exit 0
fi

if ! command -v dockerd >/dev/null 2>&1; then
  echo "dockerd is not installed" >&2
  exit 1
fi

sudo mkdir -p /etc/docker
if [[ ! -f /etc/docker/daemon.json ]]; then
  printf '%s\n' '{"storage-driver":"vfs"}' | sudo tee /etc/docker/daemon.json >/dev/null
fi

sudo update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true

if ! pgrep -x dockerd >/dev/null 2>&1; then
  sudo dockerd >/tmp/dockerd.log 2>&1 &
fi

for _ in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
  if [[ -S /var/run/docker.sock ]]; then
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
  fi
    exit 0
  fi
  sleep 1
done

echo "Docker daemon failed to become ready" >&2
tail -20 /tmp/dockerd.log >&2 || true
exit 1
