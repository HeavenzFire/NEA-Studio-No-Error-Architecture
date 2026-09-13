# 🚀 Pilot Deployment Operational Checklist

**Version:** 1.0  
**Date:** $(date +%Y-%m-%d)  
**Status:** Ready for Bronze/Silver Tier Deployment  

---

## ✅ Pre-Deployment Verification

### 1. Environment Stack Validation
- [ ] Debian 12 host confirmed (`cat /etc/debian_version`)
- [ ] Node.js v20.19.5+ installed (`node --version`)
- [ ] Python 3.12.10+ installed (`python3 --version`)
- [ ] Git 2.39.5+ initialized (`git --version`)
- [ ] `/workspace` directory contains all artifacts

### 2. Core Engine Verification
- [ ] `hyper_simulation_engine.py` executed successfully (100K events, 10x compression)
- [ ] `epoch_scale_simulation.py` validated (177K adaptations, 0 Phase Lock violations)
- [ ] `simulation_results.json` archived with generation progression data
- [ ] Compression algorithms tested (DeltaEncoder, SwarmBloomFilter, HierarchicalAggregator)

### 3. Resilience Layer Status
- [ ] Phase 5 scripts deployed to `/usr/local/bin/`:
  - [ ] `health-check.sh` - System health monitoring
  - [ ] `auto-recover.sh` - Automated recovery procedures
  - [ ] `log-incident.sh` - Incident documentation
  - [ ] `create-snapshot.sh` - State capture
  - [ ] `health-check-loop.sh` - Continuous monitoring daemon
- [ ] Systemd services configured:
  - [ ] `health-monitor.service` enabled and running
  - [ ] `resource-monitor.service` (if applicable)
- [ ] Resilience directories created:
  - [ ] `/root/dev/src/resilience/health-checks/`
  - [ ] `/root/dev/src/resilience/recovery-scripts/`
  - [ ] `/root/dev/src/resilience/incident-log/`
  - [ ] `/root/dev/src/resilience/snapshots/`

### 4. Backup Matrix Configuration
- [ ] **CRITICAL:** Update `DEST` path in `backup-matrix.sh`
  - Current: `/mnt/secondary_drive/backups`
  - Action: Modify to match actual secondary drive mount point
- [ ] GPG encryption keys generated (`gpg --gen-key`)
- [ ] Test backup executed successfully
- [ ] Backup restoration tested (decrypt + extract)
- [ ] Cron job configured for automated backups:
  ```bash
  crontab -l | grep backup-matrix || echo "0 2 * * * /usr/local/bin/backup-matrix.sh" | crontab -
  ```

---

## 🔧 Systemd Dependency Resolution

### Issue: systemctl commands require systemd
The current environment may be running in a container without full systemd support.

**Resolution Steps:**
1. Check if systemd is available:
   ```bash
   which systemctl && systemctl --version
   ```

2. If missing, install systemd utilities:
   ```bash
   apt-get update && apt-get install -y systemd systemd-sysv
   ```

3. For container environments without systemd:
   - Use `supervisord` as alternative process manager
   - Deploy health checks via cron instead of systemd timers
   - Run recovery scripts as background daemons

4. Alternative health monitoring (cron-based):
   ```bash
   # Add to crontab
   */5 * * * * /usr/local/bin/health-check.sh >> /var/log/local-dev/health-cron.log 2>&1
   0 * * * * /usr/local/bin/auto-recover.sh >> /var/log/local-dev/recovery-cron.log 2>&1
   ```

---

## 📊 Error Log Analysis

### Load Test Errors (110 flagged)
**Action Required:** Root cause analysis of latency spikes

**Investigation Steps:**
1. Locate error logs:
   ```bash
   find /workspace -name "*.log" -o -name "*error*" | grep -v node_modules
   ```

2. Analyze error patterns:
   ```bash
   grep -r "ERROR\|CRITICAL\|FAIL" /var/log/local-dev/ 2>/dev/null | head -50
   ```

3. Common causes to investigate:
   - Memory pressure during high EPS tests
   - Database connection pool exhaustion
   - Network socket limits
   - Compression algorithm bottlenecks

4. Remediation actions:
   - [ ] Increase memory limits if OOM detected
   - [ ] Tune database connection pooling
   - [ ] Optimize compression buffer sizes
   - [ ] Implement circuit breakers for flood scenarios

---

## 🏗️ Pilot Environment Deployment

### Bronze Tier Partners (Basic Simulation)
**Capabilities:**
- Local hyper-simulation engine (10K events/sec)
- Basic resilience layer (health checks + snapshots)
- Daily encrypted backups
- Community support channel

**Deployment Steps:**
1. Clone repository:
   ```bash
   git clone <repo-url> && cd workspace
   ```

2. Run initialization:
   ```bash
   ./init-debian-node.sh
   ./phase5-resilience-layer.sh
   ```

3. Configure backup destination in `backup-matrix.sh`

4. Execute test simulation:
   ```bash
   python3 hyper_simulation_engine.py --events 10000
   ```

5. Verify resilience layer:
   ```bash
   health-check
   create-snapshot
   ```

### Silver Tier Partners (Advanced Evolution)
**Capabilities:**
- Epoch-scale simulation (100K+ years compressed)
- Full adversarial evolution engine
- Real-time incident logging
- Priority support + monthly architecture review

**Additional Steps:**
1. Install additional dependencies:
   ```bash
   pip3 install numpy scipy matplotlib
   npm install --save dev dependencies
   ```

2. Configure adversarial evolution parameters:
   ```bash
   cp .env.example .env.local
   # Edit EVOLUTION_RATE, MUTATION_FACTOR, LAMBDA_PRESSURE
   ```

3. Run epoch-scale validation:
   ```bash
   python3 epoch_scale_simulation.py --cycles 500000
   ```

4. Archive results to Zenodo:
   - Generate DOI for reproducibility
   - Upload simulation logs, adversarial reports, load test outputs

---

## 📦 Artifact Archival (Zenodo Deployment)

### Required Artifacts for DOI Registration
1. **Simulation Logs:**
   - `simulation_results.json`
   - Health check logs (`health_*.log`)
   - Incident reports (`incident-log/*.md`)

2. **Adversarial Reports:**
   - Threat strategy mappings (26 strategies discovered)
   - Convergent evolution analysis (36 convergences)
   - Vulnerability flags and remediations

3. **Load Test Outputs:**
   - EPS ramp-up metrics
   - Latency spike analysis
   - Memory stability graphs
   - Compression throughput benchmarks

4. **Code Snapshots:**
   - Tagged Git release: `git tag -a v1.0-pilot -m "Pilot Deployment"`
   - Export archive: `git archive --format=tar.gz --output=pilot-v1.0.tar.gz v1.0-pilot`

### Zenodo Upload Process
```bash
# 1. Create Zenodo deposit (web interface or API)
# 2. Upload artifacts
# 3. Add metadata:
#    - Title: "Sovereign Labyrinth Hyper-Simulation Framework v1.0"
#    - Authors: [Your name/institution]
#    - Description: "Epoch-scale swarm evolution simulation with Phase Lock integrity"
#    - Keywords: hyper-simulation, swarm-evolution, phase-lock, resilience
# 4. Publish and receive DOI
```

---

## 🎯 Go/No-Go Decision Matrix

| Criteria | Bronze Tier | Silver Tier | Status |
|----------|-------------|-------------|--------|
| Environment initialized | ✅ Required | ✅ Required | READY |
| Resilience layer deployed | ✅ Required | ✅ Required | READY |
| Backup matrix configured | ✅ Required | ✅ Required | ⚠️ ACTION NEEDED |
| Systemd/cron monitoring | ✅ Required | ✅ Required | ⚠️ VERIFY |
| Error log analysis | ⚠️ Recommended | ✅ Required | PENDING |
| Zenodo archival | ❌ Optional | ✅ Required | PENDING |
| Adversarial evolution | ❌ Optional | ✅ Required | READY |
| Epoch-scale simulation | ❌ Optional | ✅ Required | READY |

---

## 🚨 Critical Actions Before Pilot Launch

1. **IMMEDIATE:** Update `backup-matrix.sh` DEST path
   ```bash
   sed -i 's|/mnt/secondary_drive/backups|/your/actual/backup/path|g' /workspace/backup-matrix.sh
   ```

2. **HIGH PRIORITY:** Resolve systemd dependency or deploy cron alternative
   ```bash
   # Check systemd availability
   systemctl --version || echo "Systemd not available - use cron fallback"
   ```

3. **MEDIUM PRIORITY:** Analyze 110 load test errors
   ```bash
   # Locate and analyze error logs
   find /var/log -name "*.log" -mtime -1 -exec grep -l "ERROR" {} \;
   ```

4. **STANDARD:** Test full backup/restore cycle
   ```bash
   /usr/local/bin/backup-matrix.sh
   # Then restore to temp directory and verify integrity
   ```

---

## 📞 Support Escalation Path

**Tier 1 (Self-Service):**
- Review `DEPLOYMENT_GUIDE.md`
- Check health logs: `show-health`
- Run auto-recovery: `auto-recover`

**Tier 2 (Community):**
- Post incident report: `log-incident "medium" "Issue Title" "Description"`
- Share snapshot: `create-snapshot` and upload to support channel

**Tier 3 (Core Team):**
- Emergency contact for critical failures
- Architecture review for systemic issues
- Formal safety case escalation

---

## ✅ Final Sign-Off

**Deployment Engineer:** _________________  
**Date:** _________________  
**Pilot Tier:** ☐ Bronze ☐ Silver  

**Checklist Complete:** ☐ YES ☐ NO (with exceptions noted above)

**Next Review Date:** _________________ (30 days from deployment)

---

*This checklist is part of the Sovereign Labyrinth Formal Safety Case documentation.*  
*Revision history tracked in Git under `docs/pilot-checklist.md`*
