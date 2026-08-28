# 🛡 LOCAL COMMAND CENTER - DEBIAN 12 + NODE.JS/TYPESCRIPT STACK

## Zero Cloud Dependency | Fully Auditable | Raw Throughput Optimized

### Environment Detected
- **OS:** Debian GNU/Linux 12 (bookworm)
- **Primary Stack:** Node.js v20.19.5 + TypeScript
- **Secondary Stack:** Python 3.12.10, Go 1.19.8
- **Hypervisor:** KVM (Kernel-based Virtual Machine)

---

## 📦 DELIVERABLES

| File | Purpose | Location |
|------|---------|----------|
| `init-debian-node.sh` | Master initialization script | `/workspace/` |
| `system-init.sh` | Daily systemd optimizer | `/usr/local/bin/` |
| `backup-matrix.sh` | Encrypted backup routine | `/usr/local/bin/` |
| `dev-command-center.xml` | KVM VM configuration | `/workspace/` |

---

## 🚀 QUICK START

### Step 1: Execute Initialization
```bash
sudo bash /workspace/init-debian-node.sh
```

### Step 2: Verify Services
```bash
# Check daily optimizer timer
sudo systemctl status dev-optimizer.timer

# Check resource monitoring daemon
sudo systemctl status resource-monitor.service

# View audit logs
tail -f /var/log/local-dev/audit.log
```

### Step 3: Configure Backup Destination
Edit `/usr/local/bin/backup-matrix.sh` and change:
```bash
DEST="/mnt/secondary_drive/backups"  # Your actual secondary drive path
```

Then test:
```bash
sudo bash /usr/local/bin/backup-matrix.sh
```

### Step 4: Setup KVM Virtual Machine (Optional)
```bash
# Create disk image
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/dev-command-center.qcow2 50G

# Import VM definition
sudo virsh define /workspace/dev-command-center.xml

# Start VM
sudo virsh start dev-command-center

# Connect via VNC
virt-viewer dev-command-center
```

---

## 📊 DIRECTORY STRUCTURE

After initialization:
```
/home/$USER/dev/
├── src/                    # Source code repositories
│   ├── local-command-center/
│   └── requirements.txt
├── build/                  # Build artifacts (auto-cleaned after 7 days)
├── archive/                # Long-term storage
├── metrics/                # Performance & code metrics
│   ├── resource.csv        # Live resource monitoring
│   ├── loc_YYYY-MM-DD.csv  # Lines of code tracking
│   └── builds_YYYY-MM-DD.txt
└── local-mirror/           # Air-gapped dependencies
    ├── pypi/               # Python packages
    ├── npm/                # Node modules cache
    └── deb/                # System packages

/var/log/local-dev/
├── audit.log               # System initialization logs
└── backup.log              # Backup operation logs

/srv/git/
└── local-command-center.git  # Bare Git repository
```

---

## 🔧 SYSTEMD SERVICES

| Service | Type | Schedule | Purpose |
|---------|------|----------|---------|
| `dev-optimizer.timer` | Timer | Daily | Directory cleanup, service verification |
| `dev-optimizer.service` | Oneshot | Triggered by timer | Executes system-init.sh |
| `resource-monitor.service` | Daemon | Continuous | Logs CPU/Memory every 5 seconds |

---

## 🔐 SECURITY FEATURES

1. **Local-Only Git Repository**
   - No outbound calls to GitHub/GitLab
   - Pre-commit hooks enforce linting (shellcheck, eslint, black)

2. **Air-Gapped Dependencies**
   - Python: `pip download` mirrors to `~/dev/local-mirror/pypi`
   - Node: npm cache configured to local directory
   - Set `npm config set offline true` after initial mirror

3. **Encrypted Backups**
   - AES-256 symmetric encryption via GPG
   - Automatic pruning after 30 days

4. **Audit Logging**
   - All operations logged with ISO-8601 timestamps
   - Centralized log location: `/var/log/local-dev/`

---

## 📈 METRICS TRACKING

### Resource Monitoring (Live)
```bash
tail -f ~/dev/metrics/resource.csv
```
Format: `timestamp,cpu_user,cpu_system,mem_used_mb`

### Code Metrics (Daily at 23:00)
```bash
cat ~/dev/metrics/loc_$(date +%F).csv
cat ~/dev/metrics/builds_$(date +%F).txt
```

Install `cloc` for enhanced LOC tracking:
```bash
sudo apt install cloc -y
```

---

## ⚙ CRON JOBS

| Schedule | Command | Purpose |
|----------|---------|---------|
| `0 23 * * *` | `/usr/local/bin/daily-metrics.sh` | Collect daily code metrics |

View cron table:
```bash
crontab -l
```

---

## 🛠 TROUBLESHOOTING

### KVM Not Starting
```bash
# Check KVM module
lsmod | grep kvm

# Load if missing
sudo modprobe kvm_intel  # or kvm_amd for AMD CPUs

# Verify libvirt
sudo systemctl status libvirtd
```

### Dependency Mirror Issues
```bash
# Manually mirror Python packages
cd ~/dev/src
pip download -r requirements.txt -d ~/dev/local-mirror/pypi

# Clear npm cache and re-mirror
npm cache clean --force
npm config set cache ~/dev/local-mirror/npm
```

### Service Failures
```bash
# View detailed logs
journalctl -u dev-optimizer.service -n 50
journalctl -u resource-monitor.service -n 50
```

---

## 🎯 NEXT STEPS

1. [ ] Modify `backup-matrix.sh` with your secondary drive path
2. [ ] Run initialization: `sudo bash init-debian-node.sh`
3. [ ] Verify all services: `systemctl list-units | grep dev-`
4. [ ] Clone your projects into `~/dev/src/`
5. [ ] Configure npm offline mode after mirroring
6. [ ] (Optional) Deploy KVM VM for isolated development

---

## 📝 MAINTENANCE

### Weekly
- Review audit logs: `less /var/log/local-dev/audit.log`
- Verify backup integrity: `gpg --decrypt backup.tar.gz.gpg`

### Monthly
- Archive old metrics: `gzip ~/dev/metrics/*.csv`
- Update dependency mirrors (if internet access available)

### Quarterly
- Rotate encryption keys for backups
- Review and optimize VM resource allocation

---

**Generated:** $(date -Iseconds)  
**Stack:** Debian 12 + Node.js/TypeScript + Python + Go  
**Architecture:** Zero Cloud | Local-First | Audit-Ready
