#!/bin/bash
set -euo pipefail

# =============================================================================
# BACKUP MATRIX SCRIPT - Redundant Local Backup with Encryption
# Location: /usr/local/bin/backup-matrix.sh
# Configure DEST according to your secondary drive path
# =============================================================================

SOURCE="$HOME/dev"
DEST="/mnt/secondary_drive/backups"  # MODIFY THIS for your setup
DATE=$(date +%Y%m%d_%H%M%S)
ARCHIVE="$DEST/project_$DATE.tar.gz.gpg"
LOG_FILE="/var/log/local-dev/backup.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date -Iseconds)] BACKUP START"

# Ensure destination exists
mkdir -p "$DEST"

# Create encrypted backup
if [ -d "$SOURCE" ]; then
    tar -czf - "$SOURCE" | gpg --symmetric --cipher-algo AES256 --batch --yes -o "$ARCHIVE"
    echo "[$(date -Iseconds)] Backup complete: $ARCHIVE"
else
    echo "[$(date -Iseconds)] ERROR: Source directory $SOURCE does not exist"
    exit 1
fi

# Prune backups older than 30 days
find "$DEST" -name "*.gpg" -mtime +30 -delete
echo "[$(date -Iseconds)] Pruned backups older than 30 days"

echo "[$(date -Iseconds)] BACKUP COMPLETE"
