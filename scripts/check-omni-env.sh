#!/bin/bash
set -euo pipefail
docker exec -i topicai-backend python -e PYTHONPATH=/app /dev/stdin < /tmp/check_omni_env.py
