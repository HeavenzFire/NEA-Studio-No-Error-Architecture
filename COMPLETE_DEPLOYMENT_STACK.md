# 🛡 Local Command Center - Complete Deployment Stack

## Zero Cloud Dependency | Fully Auditable | Raw Throughput Optimized

---

## 📦 Phase Summary

| Phase | Component | Status | Script |
|-------|-----------|--------|--------|
| **Phase 1** | Environment Hardening & Isolation | ✅ Ready | `init-debian-node.sh` |
| **Phase 2** | Automation & Orchestration | ✅ Ready | `system-init.sh`, `backup-matrix.sh` |
| **Phase 3** | Metric Tracking & Performance | ✅ Integrated | Resource monitor daemon |
| **Phase 4** | Accountability Engine | ✅ Ready | `phase4-accountability-engine.sh` |
| **Phase 5** | Resilience Layer & Self-Healing | ✅ Ready | `phase5-resilience-layer.sh` |

---

## 🚀 Quick Start - One Command Deployment

```bash
# Execute complete initialization stack
sudo bash /workspace/init-debian-node.sh && \
sudo bash /workspace/phase4-accountability-engine.sh && \
sudo bash /workspace/phase5-resilience-layer.sh
```

---

## 📁 File Inventory

### Core Initialization Scripts
| File | Size | Purpose |
|------|------|---------|
| `init-debian-node.sh` | 8.4K | Master initialization (directories, Git, KVM, systemd) |
| `system-init.sh` | 991B | Daily optimizer called by systemd timer |
| `backup-matrix.sh` | 1.2K | AES-256 encrypted backup routine |

### Phase 4: Accountability Engine
| File | Purpose |
|------|---------|
| `phase4-accountability-engine.sh` | Deploys accountability protocols |
| `/usr/local/bin/log-decision.sh` | Log architectural decisions with full context |
| `/usr/local/bin/log-refusal.sh` | Track refused requests with rationale |
| `/usr/local/bin/convene-council.sh` | Initiate council review process |
| `/usr/local/bin/track-lineage.sh` | Capture artifact lineage with checksums |
| `/usr/local/bin/generate-accountability-report.sh` | Weekly HTML dashboard |

### Phase 5: Resilience Layer
| File | Purpose |
|------|---------|
| `phase5-resilience-layer.sh` | Deploys self-healing protocols |
| `/usr/local/bin/health-check.sh` | System health assessment (disk, memory, services) |
| `/usr/local/bin/auto-recover.sh` | Automated recovery procedures |
| `/usr/local/bin/log-incident.sh` | Incident tracking with severity levels |
| `/usr/local/bin/create-snapshot.sh` | State capture for forensics |
| `/usr/local/bin/health-check-loop.sh` | 60-second interval monitoring daemon |

### Configuration Files
| File | Purpose |
|------|---------|
| `dev-command-center.xml` | KVM VM definition (4 vCPU, 8GB RAM, CPU pinning) |
| `/etc/systemd/system/dev-optimizer.service` | Daily optimization service |
| `/etc/systemd/system/dev-optimizer.timer` | Daily trigger (Persistent=true) |
| `/etc/systemd/system/resource-monitor.service` | 5-second metric collection |
| `/etc/systemd/system/health-monitor.service` | 60-second health monitoring |

---

## 🎯 Available Commands (Post-Deployment)

### Accountability Commands
```bash
log-decision "Migrated to SQLite" "PostgreSQL, BoltDB" "Lower overhead" "high"
log-refusal "Enable telemetry" "Violates zero-cloud policy" "Local metrics only"
convene-council "Architecture Review" "urgent"
track-lineage "parent_123" "/path/to/artifact" "transformation_type"
accountability-report  # Generates weekly HTML dashboard
```

### Resilience Commands
```bash
health-check         # Manual health assessment
auto-recover         # Execute recovery procedures
log-incident "critical" "Service Outage" "Description" "Actions taken"
create-snapshot      # Capture system state
show-health          # Tail today's health log
list-snapshots       # Show recent 10 snapshots
```

### Monitoring Commands
```bash
show-metrics         # Live resource CSV tail
audit-log            # Live audit log tail
```

---

## 📊 Directory Structure Created

```
~/dev/
├── src/
│   ├── local-command-center/    # Main working repository
│   ├── accountability/
│   │   ├── decisions/           # Decision records (.md)
│   │   ├── refusals/            # Refusal logs (.md)
│   │   ├── council/             # Council reviews
│   │   └── archive/             # Archived records
│   ├── lineage/                 # Artifact lineage (JSON)
│   ├── resilience/
│   │   ├── health-checks/       # Daily health logs
│   │   ├── recovery-scripts/    # Recovery execution logs
│   │   ├── incident-log/        # Incident reports (.md)
│   │   └── snapshots/           # Compressed state captures
│   └── requirements.txt         # Python dependencies
├── build/                       # Temporary build artifacts (7-day retention)
├── archive/                     # Long-term storage
├── metrics/
│   ├── resource.csv             # 5-second CPU/Memory logs
│   ├── loc_YYYY-MM-DD.csv       # Daily code line counts
│   └── builds_YYYY-MM-DD.txt    # Daily commit counts
├── local-mirror/
│   ├── pypi/                    # Cached Python packages
│   ├── npm/                     # Cached Node modules
│   └── deb/                     # Cached Debian packages
└── public-accountability/       # Generated HTML reports

/srv/git/
└── local-command-center.git     # Bare Git repository

/var/log/local-dev/
├── audit.log                    # Main audit trail
├── backup.log                   # Backup execution logs
└── *.log.old.gz                 # Rotated compressed logs
```

---

## 🔧 Customization Points

### 1. Backup Destination
Edit `backup-matrix.sh` line 11:
```bash
DEST="/mnt/secondary_drive/backups"  # Change to your path
```

### 2. Health Check Thresholds
Edit `/usr/local/bin/health-check.sh`:
```bash
if [ "$DISK_USAGE" -gt 90 ]; then  # Adjust percentage
if [ "$MEM_USAGE" -gt 90 ]; then   # Adjust percentage
```

### 3. Monitoring Intervals
- Resource monitor: Edit `sleep 5` in `/usr/local/bin/resource-monitor.sh`
- Health monitor: Edit `sleep 60` in `/usr/local/bin/health-check-loop.sh`

### 4. Retention Policies
- Build artifacts: 7 days (edit `system-init.sh` line 20)
- Metrics CSV: 30 days before gzip (edit `system-init.sh` line 24)
- Backups: 30 days (edit `backup-matrix.sh` line 33)

---

## 🔐 Security Features

| Feature | Implementation |
|---------|----------------|
| **Encryption** | GPG AES-256 for all backups |
| **Isolation** | KVM hypervisor with CPU pinning |
| **Audit Trail** | ISO-8601 timestamps on all logs |
| **Access Control** | Pre-commit hooks enforce linting |
| **Air-Gap Ready** | Offline dependency mirrors (PyPI, npm, deb) |
| **No Cloud Calls** | Zero outbound connections for core ops |

---

## 📈 Active Services

| Service | Type | Interval | Purpose |
|---------|------|----------|---------|
| `resource-monitor.service` | Daemon | 5 seconds | CPU/Memory logging |
| `dev-optimizer.timer` | Timer | Daily | Cleanup & maintenance |
| `health-monitor.service` | Daemon | 60 seconds | Health checks + auto-recovery |

### Verify Services
```bash
sudo systemctl status dev-optimizer.timer
sudo systemctl status resource-monitor.service
sudo systemctl status health-monitor.service
```

---

## 🗓 Cron Jobs

| Schedule | Command | Purpose |
|----------|---------|---------|
| `0 23 * * *` | `/usr/local/bin/daily-metrics.sh` | Daily LOC & commit metrics |
| `0 8 * * 1` | `/usr/local/bin/generate-accountability-report.sh` | Weekly accountability report |

---

## 🛠 Troubleshooting

### Service Not Running
```bash
sudo systemctl daemon-reload
sudo systemctl restart <service-name>
sudo systemctl status <service-name>
```

### Disk Space Critical
```bash
auto-recover  # Clears old artifacts and rotates logs
find ~/dev/build -type f -mtime +7 -delete
```

### Git Repository Corruption
```bash
cd ~/dev/src/local-command-center
git fsck --full
git gc --prune=now
```

### Restore from Backup
```bash
# Find backup file
ls -lht /mnt/secondary_drive/backups/*.gpg | head

# Decrypt and extract
gpg --decrypt backup_YYYYMMDD_HHMMSS.tar.gz.gpg | tar -xzf -
```

---

## 📋 Post-Deployment Checklist

- [ ] Edit `backup-matrix.sh` with actual secondary drive path
- [ ] Verify all systemd services are active
- [ ] Run manual health check: `health-check`
- [ ] Create test decision: `log-decision "Test" "N/A" "Validation" "low"`
- [ ] Generate accountability report: `accountability-report`
- [ ] Configure npm offline mode after initial mirror: `npm config set offline true`
- [ ] (Optional) Deploy isolated VM using `dev-command-center.xml`

---

## 🎯 Architecture Principles

1. **Zero Trust Local**: Assume no external service is available
2. **Full Auditability**: Every action logged with ISO-8601 timestamps
3. **Raw Throughput**: KVM with CPU pinning, no virtualization overhead
4. **Self-Healing**: Automated detection and recovery from failures
5. **Accountability First**: All decisions tracked with context and rationale

---

## 📞 Quick Reference Card

```bash
# === ACCOUNTABILITY ===
log-decision "context" "alternatives" "rationale" "impact"
log-refusal "request" "reason" "alternative"
convene-council "topic" [urgency]
track-lineage [parent_id] [artifact_path] [transformation]

# === RESILIENCE ===
health-check          # Check system health
auto-recover          # Auto-fix issues
log-incident "severity" "title" "description" "actions"
create-snapshot       # Capture state

# === MONITORING ===
show-metrics          # Live resource usage
audit-log             # Live audit trail
show-health           # Today's health log
list-snapshots        # Recent snapshots

# === SYSTEM ===
sudo systemctl status dev-optimizer.timer
sudo systemctl status resource-monitor.service
sudo systemctl status health-monitor.service
```

---

*Generated: $(date -Iseconds)*  
*Local Command Center - Complete Deployment Stack*  
*Zero Cloud | Fully Auditable | Maximum Throughput*
