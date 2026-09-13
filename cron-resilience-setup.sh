#!/bin/bash
set -euo pipefail

# =============================================================================
# CRON-BASED RESILIENCE LAYER (Systemd Alternative)
# For container environments without systemd support
# =============================================================================

echo "[$(date -Iseconds)] Setting up cron-based resilience layer..."

# Create log directory
mkdir -p /var/log/local-dev

# Install cron if not present
if ! command -v cron &> /dev/null; then
    echo "Installing cron..."
    apt-get update && apt-get install -y cron
fi

# Ensure resilience directories exist
RESILIENCE_DIR="$HOME/dev/src/resilience"
mkdir -p "$RESILIENCE_DIR"/{health-checks,recovery-scripts,incident-log,snapshots}

# Deploy health check cron job
cat > /tmp/health-cron << 'CRON'
*/5 * * * * /usr/local/bin/health-check.sh >> /var/log/local-dev/health-cron.log 2>&1
0 * * * * /usr/local/bin/auto-recover.sh >> /var/log/local-dev/recovery-cron.log 2>&1
0 2 * * * /usr/local/bin/backup-matrix.sh >> /var/log/local-dev/backup-cron.log 2>&1
CRON

# Install cron jobs
crontab /tmp/health-cron
rm /tmp/health-cron

# Restart cron service
service cron restart || /etc/init.d/cron restart || cron

echo "[$(date -Iseconds)] Cron-based resilience layer deployed"
echo ""
echo "Active cron jobs:"
crontab -l
echo ""
echo "Log files:"
echo "  /var/log/local-dev/health-cron.log"
echo "  /var/log/local-dev/recovery-cron.log"
echo "  /var/log/local-dev/backup-cron.log"
