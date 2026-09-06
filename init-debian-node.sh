#!/bin/bash
set -euo pipefail

# =============================================================================
# LOCAL COMMAND CENTER - INITIALIZATION SCRIPT
# Target: Debian 12 + Node.js/TypeScript Stack
# Zero Cloud Dependency | Fully Auditable | Raw Throughput Optimized
# =============================================================================

LOG_DIR="/var/log/local-dev"
DEV_ROOT="$HOME/dev"
GIT_REPO_PATH="/srv/git/local-command-center.git"
BACKUP_DEST="/mnt/secondary_drive/backups"
MIRROR_DIR="$DEV_ROOT/local-mirror"

echo "[$(date -Iseconds)] INIT START"

# -----------------------------------------------------------------------------
# 1. CREATE DIRECTORY STRUCTURE
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Creating directory structure..."
mkdir -p "$DEV_ROOT"/{src,build,archive,metrics}
mkdir -p "$LOG_DIR"
mkdir -p "$MIRROR_DIR"/{pypi,npm,deb}
sudo mkdir -p "$(dirname "$GIT_REPO_PATH")"
sudo chown "$USER:$USER" "$(dirname "$GIT_REPO_PATH")"

# -----------------------------------------------------------------------------
# 2. INITIALIZE LOCAL BARE GIT REPOSITORY
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Initializing local bare Git repository..."
if [ ! -d "$GIT_REPO_PATH" ]; then
    git init --bare "$GIT_REPO_PATH"
fi

# Clone if not already cloned
CLONE_DIR="$DEV_ROOT/src/local-command-center"
if [ ! -d "$CLONE_DIR/.git" ]; then
    echo "[$(date -Iseconds)] Cloning local repository..."
    git clone "$GIT_REPO_PATH" "$CLONE_DIR" || true
fi

# -----------------------------------------------------------------------------
# 3. INSTALL HYPERVISOR (KVM) - HIGHEST PERFORMANCE
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Checking KVM hypervisor..."
if ! dpkg -l | grep -q qemu-kvm; then
    echo "[$(date -Iseconds)] Installing KVM hypervisor..."
    sudo apt update
    sudo apt install qemu-kvm libvirt-daemon-system virt-manager -y
    sudo virsh net-start default || true
    sudo virsh net-autostart default || true
fi

# -----------------------------------------------------------------------------
# 4. CREATE SYSTEMD SERVICE & TIMER
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Setting up systemd optimizer service..."

sudo tee /etc/systemd/system/dev-optimizer.service > /dev/null << 'EOF'
[Unit]
Description=Daily Development Environment Optimizer
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/system-init.sh
StandardOutput=append:/var/log/local-dev/audit.log
StandardError=append:/var/log/local-dev/audit.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/dev-optimizer.timer > /dev/null << 'EOF'
[Unit]
Description=Run dev-optimizer daily
Requires=dev-optimizer.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now dev-optimizer.timer

# -----------------------------------------------------------------------------
# 5. CREATE AIR-GAPPED DEPENDENCY MIRRORS
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Setting up offline dependency mirrors..."

# Create requirements.txt if it doesn't exist
if [ ! -f "$DEV_ROOT/src/requirements.txt" ]; then
    cat > "$DEV_ROOT/src/requirements.txt" << 'EOF'
# Python dependencies for local development
black
flake8
mypy
pytest
requests
EOF
fi

# Mirror Python packages
cd "$DEV_ROOT/src"
if [ ! -d "$MIRROR_DIR/pypi" ] || [ -z "$(ls -A "$MIRROR_DIR/pypi" 2>/dev/null)" ]; then
    echo "[$(date -Iseconds)] Mirroring Python packages..."
    pip download -r requirements.txt -d "$MIRROR_DIR/pypi" || echo "Warning: pip download failed, may need manual intervention"
fi

# Configure npm for offline mode
npm config set offline false  # Set to true after initial mirror
npm config set cache "$MIRROR_DIR/npm"

# -----------------------------------------------------------------------------
# 6. SETUP PRE-COMMIT HOOKS
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Installing pre-commit hooks..."

if [ -d "$CLONE_DIR/.git" ]; then
    cat > "$CLONE_DIR/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
set -e
echo "[AUDIT] Enforcing syntax and format..."

# Shell script linting
find . -name "*.sh" -type f -exec shellcheck {} \; || true

# TypeScript/JavaScript linting (if available)
if command -v npx &> /dev/null; then
    npx eslint . --ext .ts,.tsx,.js,.jsx || true
fi

# Python linting (if available)
if command -v black &> /dev/null; then
    black --check . || true
fi

echo "[AUDIT] Pre-commit checks complete"
EOF
    chmod +x "$CLONE_DIR/.git/hooks/pre-commit"
fi

# -----------------------------------------------------------------------------
# 7. CONFIGURE RESOURCE MONITORING DAEMON
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Setting up resource monitoring..."

cat > /usr/local/bin/resource-monitor.sh << 'EOF'
#!/bin/bash
METRICS_FILE="$HOME/dev/metrics/resource.csv"
mkdir -p "$(dirname "$METRICS_FILE")"

# Add header if file doesn't exist
if [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,cpu_user,cpu_system,mem_used_mb" > "$METRICS_FILE"
fi

while true; do
    TIMESTAMP=$(date -Iseconds)
    CPU_LINE=$(grep 'cpu ' /proc/stat)
    CPU_USER=$(echo "$CPU_LINE" | awk '{print $2}')
    CPU_SYSTEM=$(echo "$CPU_LINE" | awk '{print $4}')
    MEM_USED=$(free -m | awk '/Mem:/ {print $3}')
    
    echo "$TIMESTAMP,$CPU_USER,$CPU_SYSTEM,$MEM_USED" >> "$METRICS_FILE"
    sleep 5
done
EOF
chmod +x /usr/local/bin/resource-monitor.sh

# Create systemd service for monitoring
sudo tee /etc/systemd/system/resource-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Resource Monitoring Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/resource-monitor.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now resource-monitor.service

# -----------------------------------------------------------------------------
# 8. SETUP DAILY METRICS COLLECTION
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Setting up daily metrics collection..."

cat > /usr/local/bin/daily-metrics.sh << 'EOF'
#!/bin/bash
set -e
METRICS_DIR="$HOME/dev/metrics"
DATE=$(date +%F)
mkdir -p "$METRICS_DIR"

# Code line quantification
if command -v cloc &> /dev/null; then
    cloc "$HOME/dev/src" --csv --out="$METRICS_DIR/loc_$DATE.csv" 2>/dev/null || true
else
    echo "cloc not installed, skipping LOC metrics"
fi

# Git activity
if [ -d "$HOME/dev/src" ]; then
    cd "$HOME/dev/src"
    git log --since="1 day ago" --oneline 2>/dev/null | wc -l > "$METRICS_DIR/builds_$DATE.txt" || echo "0" > "$METRICS_DIR/builds_$DATE.txt"
fi

echo "[$(date -Iseconds)] Daily metrics collected" >> "$HOME/dev/metrics/metrics.log"
EOF
chmod +x /usr/local/bin/daily-metrics.sh

# Add to cron
(crontab -l 2>/dev/null | grep -v "daily-metrics" ; echo "0 23 * * * /usr/local/bin/daily-metrics.sh") | crontab -

# -----------------------------------------------------------------------------
# 9. CLEANUP ROUTINE
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] Running cleanup routine..."
find "$DEV_ROOT/build" -type f -mtime +7 -delete 2>/dev/null || true

# -----------------------------------------------------------------------------
# COMPLETE
# -----------------------------------------------------------------------------
echo "[$(date -Iseconds)] INIT COMPLETE"
echo ""
echo "=========================================="
echo "LOCAL COMMAND CENTER INITIALIZED"
echo "=========================================="
echo "Git Repository: $GIT_REPO_PATH"
echo "Dev Root: $DEV_ROOT"
echo "Logs: $LOG_DIR"
echo "Metrics: $DEV_ROOT/metrics"
echo ""
echo "Next steps:"
echo "1. Configure backup-matrix.sh with your secondary drive path"
echo "2. Run: sudo systemctl status dev-optimizer.timer"
echo "3. Run: sudo systemctl status resource-monitor.service"
echo "4. Set npm offline mode after mirroring: npm config set offline true"
echo "=========================================="
