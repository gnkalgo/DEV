#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://127.0.0.1/health
echo
curl -fsS http://127.0.0.1/api/v1/ready
echo
