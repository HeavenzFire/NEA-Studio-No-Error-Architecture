#!/bin/bash
set -euo pipefail

# =============================================================================
# SYSTEM INITIALIZATION SCRIPT - Called by systemd timer daily
# Location: /usr/local/bin/system-init.sh
# =============================================================================

LOG_FILE="/var/log/local-dev/audit.log"
DEV_ROOT="$HOME/dev"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date -Iseconds)] INIT START"

# Daily directory structure maintenance
mkdir -p "$DEV_ROOT"/{src,build,archive}

# Cleanup build artifacts older than 7 days
find "$DEV_ROOT/build" -type f -mtime +7 -delete 2>/dev/null || true

# Archive old metrics (optional - keep last 30 days inline)
if [ -d "$DEV_ROOT/metrics" ]; then
    find "$DEV_ROOT/metrics" -name "*.csv" -mtime +30 -exec gzip {} \; 2>/dev/null || true
fi

# Verify critical services
systemctl is-active resource-monitor.service >/dev/null || systemctl restart resource-monitor.service

echo "[$(date -Iseconds)] INIT COMPLETE"
