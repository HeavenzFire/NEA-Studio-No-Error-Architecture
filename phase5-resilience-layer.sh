#!/bin/bash
set -euo pipefail

# =============================================================================
# PHASE 5: RESILIENCE LAYER & SELF-HEALING PROTOCOLS
# Zero Cloud Dependency | Fully Auditable | Raw Throughput Optimized
# =============================================================================

LOG_DIR="/var/log/local-dev"
DEV_ROOT="$HOME/dev"
RESILIENCE_DIR="$DEV_ROOT/src/resilience"

echo "[$(date -Iseconds)] PHASE 5 INIT START"

# -----------------------------------------------------------------------------
# 5.1 CREATE RESILIENCE DIRECTORY STRUCTURE
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Creating resilience structure..."
mkdir -p "$RESILIENCE_DIR"/{health-checks,recovery-scripts,incident-log,snapshots}

# -----------------------------------------------------------------------------
# 5.2 DEPLOY HEALTH CHECK DAEMON
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Deploying health check daemon..."

cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
set -euo pipefail

HEALTH_LOG="$HOME/dev/src/resilience/health-checks/health_$(date +%Y%m%d).log"
mkdir -p "$(dirname "$HEALTH_LOG")"

TIMESTAMP=$(date -Iseconds)
STATUS="HEALTHY"
ISSUES=()

# Check disk space (alert if >90% used)
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 90 ]; then
    STATUS="CRITICAL"
    ISSUES+=("Disk usage at ${DISK_USAGE}%")
elif [ "$DISK_USAGE" -gt 80 ]; then
    STATUS="WARNING"
    ISSUES+=("Disk usage at ${DISK_USAGE}%")
fi

# Check memory (alert if >90% used)
MEM_USAGE=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 90 ]; then
    STATUS="CRITICAL"
    ISSUES+=("Memory usage at ${MEM_USAGE}%")
elif [ "$MEM_USAGE" -gt 80 ]; then
    STATUS="WARNING"
    ISSUES+=("Memory usage at ${MEM_USAGE}%")
fi

# Check critical services
for SERVICE in resource-monitor.service dev-optimizer.timer; do
    if ! systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
        STATUS="CRITICAL"
        ISSUES+=("Service $SERVICE is not running")
    fi
done

# Check log directory writability
if ! touch "$LOG_DIR/.write_test" 2>/dev/null; then
    STATUS="CRITICAL"
    ISSUES+=("Log directory not writable: $LOG_DIR")
else
    rm -f "$LOG_DIR/.write_test"
fi

# Check backup destination (if configured)
BACKUP_DEST="/mnt/secondary_drive/backups"
if [ -d "$BACKUP_DEST" ] && ! touch "$BACKUP_DEST/.write_test" 2>/dev/null; then
    STATUS="WARNING"
    ISSUES+=("Backup destination not writable: $BACKUP_DEST")
fi

# Write health status
cat >> "$HEALTH_LOG" << HEALTH
---
Timestamp: $TIMESTAMP
Status: $STATUS
Host: $(hostname)
Uptime: $(uptime -p)
Disk Usage: ${DISK_USAGE}%
Memory Usage: ${MEM_USAGE}%
HEALTH

if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "Issues Detected:" >> "$HEALTH_LOG"
    for ISSUE in "${ISSUES[@]}"; do
        echo "  - $ISSUE" >> "$HEALTH_LOG"
    done
fi

echo "$STATUS"
exit 0
EOF

chmod +x /usr/local/bin/health-check.sh

# -----------------------------------------------------------------------------
# 5.3 DEPLOY AUTOMATED RECOVERY SCRIPTS
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Deploying automated recovery scripts..."

cat > /usr/local/bin/auto-recover.sh << 'EOF'
#!/bin/bash
set -euo pipefail

RECOVERY_LOG="$HOME/dev/src/resilience/recovery-scripts/recovery_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$RECOVERY_LOG")"

exec > >(tee -a "$RECOVERY_LOG") 2>&1

echo "[$(date -Iseconds)] RECOVERY START"

# Recovery Action 1: Restart failed services
echo "Checking for failed services..."
FAILED_SERVICES=$(systemctl list-units --state=failed --no-legend | awk '{print $1}' || true)
if [ -n "$FAILED_SERVICES" ]; then
    echo "Found failed services: $FAILED_SERVICES"
    for SERVICE in $FAILED_SERVICES; do
        echo "Attempting to restart $SERVICE..."
        systemctl reset-failed "$SERVICE" 2>/dev/null || true
        systemctl start "$SERVICE" 2>/dev/null && echo "✅ $SERVICE restarted" || echo "❌ Failed to restart $SERVICE"
    done
fi

# Recovery Action 2: Clear old temporary files
echo "Cleaning temporary build artifacts..."
find "$HOME/dev/build" -type f -mtime +7 -delete 2>/dev/null || true
find "/tmp" -name "dev-*" -type f -mtime +1 -delete 2>/dev/null || true

# Recovery Action 3: Rotate large log files
echo "Rotating oversized logs..."
for LOG_FILE in /var/log/local-dev/*.log; do
    if [ -f "$LOG_FILE" ]; then
        SIZE=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$SIZE" -gt 104857600 ]; then  # 100MB
            mv "$LOG_FILE" "${LOG_FILE}.old"
            touch "$LOG_FILE"
            gzip "${LOG_FILE}.old" 2>/dev/null || true
            echo "Rotated $LOG_FILE ($(numfmt --to=iec $SIZE))"
        fi
    fi
done

# Recovery Action 4: Verify Git repository integrity
if [ -d "$HOME/dev/src/local-command-center/.git" ]; then
    echo "Verifying Git repository integrity..."
    cd "$HOME/dev/src/local-command-center"
    if ! git fsck --quiet 2>/dev/null; then
        echo "⚠️  Git repository issues detected, attempting repair..."
        git gc --prune=now 2>/dev/null || true
    else
        echo "✅ Git repository integrity verified"
    fi
fi

# Recovery Action 5: Check and restart monitoring daemon
if ! pgrep -f "resource-monitor.sh" > /dev/null; then
    echo "Resource monitor not running, restarting..."
    systemctl restart resource-monitor.service 2>/dev/null || \
    (/usr/local/bin/resource-monitor.sh &)
fi

echo "[$(date -Iseconds)] RECOVERY COMPLETE"
EOF

chmod +x /usr/local/bin/auto-recover.sh

# -----------------------------------------------------------------------------
# 5.4 DEPLOY INCIDENT LOGGING SYSTEM
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Deploying incident logging system..."

cat > /usr/local/bin/log-incident.sh << 'EOF'
#!/bin/bash
set -euo pipefail

INCIDENT_ID=$(date +%Y%m%d_%H%M%S)_$RANDOM
INCIDENT_FILE="$HOME/dev/src/resilience/incident-log/$INCIDENT_ID.md"
mkdir -p "$(dirname "$INCIDENT_FILE")"

SEVERITY="${1:-medium}"  # low, medium, high, critical
TITLE="${2:-Unspecified Incident}"
DESCRIPTION="${3:-No description provided}"
ACTIONS_TAKEN="${4:-None}"

cat > "$INCIDENT_FILE" << INCIDENT
# Incident Report: $INCIDENT_ID

**Severity:** $SEVERITY
**Title:** $TITLE
**Timestamp:** $(date -Iseconds)
**Status:** OPEN

## Description
$DESCRIPTION

## Impact Assessment
- **Services Affected:** To be determined
- **Data Loss:** None confirmed
- **Downtime:** To be determined

## Actions Taken
$ACTIONS_TAKEN

## Root Cause Analysis
[To be completed]

## Prevention Measures
[To be completed]

## Timeline
- **Detected:** $(date -Iseconds)
- **Responded:** $(date -Iseconds)
- **Resolved:** [Pending]

## Accountability Chain
- **Reporter:** $(whoami)
- **Host:** $(hostname)
- **Working Directory:** $(pwd)

---
*Auto-generated by Local Command Center Resilience System*
INCIDENT

echo "Incident logged: $INCIDENT_FILE"
echo "$INCIDENT_ID"
EOF

chmod +x /usr/local/bin/log-incident.sh

# -----------------------------------------------------------------------------
# 5.5 DEPLOY SNAPSHOT SYSTEM
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Deploying state snapshot system..."

cat > /usr/local/bin/create-snapshot.sh << 'EOF'
#!/bin/bash
set -euo pipefail

SNAPSHOT_ID=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_DIR="$HOME/dev/src/resilience/snapshots/$SNAPSHOT_ID"
mkdir -p "$SNAPSHOT_DIR"

echo "Creating system snapshot: $SNAPSHOT_ID"

# Capture process state
ps auxf > "$SNAPSHOT_DIR/processes.txt" 2>/dev/null || true

# Capture network state
netstat -tulpn > "$SNAPSHOT_DIR/network.txt" 2>/dev/null || ss -tulpn > "$SNAPSHOT_DIR/network.txt" 2>/dev/null || true

# Capture disk state
df -h > "$SNAPSHOT_DIR/disk.txt" 2>/dev/null || true
du -sh "$HOME/dev"/* > "$SNAPSHOT_DIR/dev_sizes.txt" 2>/dev/null || true

# Capture service states
systemctl list-units --state=running > "$SNAPSHOT_DIR/services.txt" 2>/dev/null || true

# Capture recent logs
tail -n 1000 /var/log/local-dev/audit.log > "$SNAPSHOT_DIR/recent_audit.log" 2>/dev/null || true

# Create manifest
cat > "$SNAPSHOT_DIR/MANIFEST.json" << MANIFEST
{
  "snapshot_id": "$SNAPSHOT_ID",
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "user": "$(whoami)",
  "kernel": "$(uname -r)",
  "uptime": "$(uptime -p)",
  "files_captured": $(find "$SNAPSHOT_DIR" -type f | wc -l)
}
MANIFEST

# Compress snapshot
cd "$SNAPSHOT_DIR/.."
tar -czf "$SNAPSHOT_ID.tar.gz" "$SNAPSHOT_ID"
rm -rf "$SNAPSHOT_DIR"

echo "Snapshot created: $SNAPSHOT_DIR/../$SNAPSHOT_ID.tar.gz"
echo "$SNAPSHOT_ID"
EOF

chmod +x /usr/local/bin/create-snapshot.sh

# -----------------------------------------------------------------------------
# 5.6 CONFIGURE AUTOMATED HEALTH MONITORING
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Configuring automated health monitoring..."

# Create systemd service for health checks
sudo tee /etc/systemd/system/health-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Health Check Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/health-check-loop.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Create health check loop script
cat > /usr/local/bin/health-check-loop.sh << 'EOF'
#!/bin/bash
set -euo pipefail

while true; do
    HEALTH_STATUS=$(/usr/local/bin/health-check.sh)
    
    if [ "$HEALTH_STATUS" = "CRITICAL" ]; then
        echo "[$(date -Iseconds)] CRITICAL health status detected!" 
        /usr/local/bin/auto-recover.sh
        /usr/local/bin/log-incident.sh "critical" "Automated Health Check Failure" "Health check returned CRITICAL status" "Triggered auto-recovery"
        /usr/local/bin/create-snapshot.sh
    elif [ "$HEALTH_STATUS" = "WARNING" ]; then
        echo "[$(date -Iseconds)] WARNING health status detected"
    fi
    
    sleep 60  # Check every minute
done
EOF

chmod +x /usr/local/bin/health-check-loop.sh

sudo systemctl daemon-reload
sudo systemctl enable --now health-monitor.service

# -----------------------------------------------------------------------------
# 5.7 CREATE QUICK REFERENCE ALIASES
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Creating shell aliases..."

cat >> ~/.bashrc << 'ALIASES'

# Local Command Center Resilience Aliases
alias health-check='/usr/local/bin/health-check.sh'
alias auto-recover='/usr/local/bin/auto-recover.sh'
alias log-incident='/usr/local/bin/log-incident.sh'
alias create-snapshot='/usr/local/bin/create-snapshot.sh'
alias show-health='tail -f ~/dev/src/resilience/health-checks/health_$(date +%Y%m%d).log'
alias list-snapshots='ls -lht ~/dev/src/resilience/snapshots/*.tar.gz | head -10'
ALIASES

source ~/.bashrc 2>/dev/null || true

# -----------------------------------------------------------------------------
# COMPLETE
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] PHASE 5 COMPLETE"
echo ""
echo "=========================================="
echo "RESILIENCE LAYER DEPLOYED"
echo "=========================================="
echo ""
echo "Available Commands:"
echo "  health-check          - Run manual health assessment"
echo "  auto-recover          - Execute automated recovery procedures"
echo "  log-incident \"severity\" \"title\" \"description\" \"actions\""
echo "  create-snapshot       - Capture current system state"
echo ""
echo "Directories Created:"
echo "  $RESILIENCE_DIR/health-checks/"
echo "  $RESILIENCE_DIR/recovery-scripts/"
echo "  $RESILIENCE_DIR/incident-log/"
echo "  $RESILIENCE_DIR/snapshots/"
echo ""
echo "Active Services:"
echo "  health-monitor.service (60-second interval)"
echo ""
echo "Quick Diagnostics:"
echo "  show-health           - Tail today's health log"
echo "  list-snapshots        - Show recent snapshots"
echo "=========================================="
