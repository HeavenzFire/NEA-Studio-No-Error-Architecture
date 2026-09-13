# Validation Reproducibility Package

## Overview

This directory contains the complete reproducibility package for the Sovereign Labyrinth Dynamic Threshold Protocol validation study.

**Purpose:** Enable independent technical reviewers to reproduce reported results from underlying evidence.

**Protocol Version:** 1.0 (see `protocol/protocol-v1.0.md`)

**Contact:** [Project Lead Contact Information]

---

## Directory Structure

```
validation/
├── README.md                    # This file
├── protocol/
│   └── protocol-v1.0.md         # Validation protocol (immutable)
├── data/
│   ├── raw/                     # Unprocessed simulation outputs
│   └── processed/               # Aggregated, analysis-ready datasets
├── config/
│   └── experiment-config.json   # All parameters, versioned and hashed
├── results/
│   ├── primary-results.json     # Primary endpoint calculations
│   ├── secondary-results.json   # Secondary endpoint metrics
│   └── statistical-analysis.json # T-test, effect size, confidence intervals
├── logs/
│   ├── execution.log            # Full run logs with timestamps
│   ├── error.log                # Captured errors and warnings
│   └── audit-trail.log          # Configuration changes, access records
├── hashes/
│   └── SHA256SUMS               # Cryptographic hashes of all artifacts
└── report/
    └── validation-report.pdf    # Final report with executive summary
```

---

## Reproduction Instructions

### Step 1: Verify Artifact Integrity

```bash
cd /workspace/validation/hashes
sha256sum -c SHA256SUMS
```

All checksums must match. If any hash fails verification, do not proceed—contact the project team immediately.

### Step 2: Review Configuration

Examine `config/experiment-config.json` to understand the exact parameters used in the validation run. Key fields:

- `temporal_scaling_factor`: 1000000 (1 real second = 1M simulated seconds)
- `cycle_count`: 500000 minimum
- `baseline_threshold`: 0.85 (static)
- `intervention`: "dynamic_threshold_protocol_v1"

### Step 3: Access Raw Data

Raw simulation outputs are stored in `data/raw/` as JSON files. Each file corresponds to one independent run:

- `run-001-raw.json` through `run-030-raw.json` (intervention group)
- `control-001-raw.json` through `control-030-raw.json` (baseline group)

### Step 4: Process Data (If Needed)

Processed datasets in `data/processed/` are provided in both CSV and Parquet formats for compatibility with common analysis tools:

```python
import pandas as pd

# Load processed data
intervention = pd.read_csv('data/processed/intervention-group.csv')
control = pd.read_csv('data/processed/control-group.csv')

# Verify collapse avoidance rate calculation
intervention_rate = intervention['collapse_avoided'].mean()
control_rate = control['collapse_avoided'].mean()
improvement = (intervention_rate - control_rate) / control_rate

print(f"Improvement: {improvement:.2%}")
```

### Step 5: Reproduce Statistical Analysis

The primary analysis uses a two-sample t-test. Recreate using:

```python
from scipy import stats
import json

# Load processed data
intervention = pd.read_csv('data/processed/intervention-group.csv')
control = pd.read_csv('data/processed/control-group.csv')

# Perform t-test
t_stat, p_value = stats.ttest_ind(
    intervention['collapse_avoidance_rate'],
    control['collapse_avoidance_rate']
)

# Calculate effect size (Cohen's d)
def cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    pooled_std = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    return (group1.mean() - group2.mean()) / pooled_std ** 0.5

effect_size = cohens_d(intervention['collapse_avoidance_rate'], control['collapse_avoidance_rate'])

# Compare with reported results
reported = json.load(open('results/statistical-analysis.json'))
assert abs(p_value - reported['p_value']) < 0.0001
assert abs(effect_size - reported['cohens_d']) < 0.01

print(f"✓ Reproduction successful: p={p_value:.4f}, d={effect_size:.3f}")
```

### Step 6: Verify Primary Endpoint

Open `results/primary-results.json` and confirm:

1. The reported collapse avoidance rate matches your calculation from raw data
2. The improvement percentage exceeds the acceptance threshold (≥10%)
3. The p-value is below 0.05

### Step 7: Sign Verification Statement

After successful reproduction, sign the verification statement using GPG:

```bash
echo "I have independently reproduced the primary endpoint calculation from the validation package. Results match reported values within tolerance." | gpg --clearsign > verification-statement.asc
```

Send `verification-statement.asc` to the project team.

---

## Acceptance Criteria for Reproduction

| Criterion | Tolerance | Status |
|-----------|-----------|--------|
| Hash verification | 100% match required | ☐ Pending |
| Primary endpoint calculation | ±0.01% | ☐ Pending |
| Statistical analysis (p-value) | ±0.0001 | ☐ Pending |
| Effect size (Cohen's d) | ±0.01 | ☐ Pending |
| Configuration hash match | Exact | ☐ Pending |

---

## Troubleshooting

### Hash Mismatch

If SHA256 verification fails:

1. Do not use the corrupted file
2. Request fresh copy from backup storage
3. Document the mismatch in an incident report

### Calculation Discrepancy

If your calculations differ from reported results by more than tolerance:

1. Verify you are using the correct data files
2. Check for missing or null values in the dataset
3. Confirm statistical method matches protocol (two-sample t-test, equal variance assumed)
4. Contact the project team with detailed discrepancy report

### Missing Files

If any expected file is missing:

1. Check the `logs/audit-trail.log` for file creation records
2. Verify backup completion status
3. Request restoration from secondary storage

---

## Retention and Access

- **Retention period:** 7 years minimum from validation completion date
- **Access level:** Available to independent reviewers, auditors, and regulatory bodies
- **Backup location:** Secondary encrypted storage (see `backup-matrix.sh`)
- **Compression:** zstd level 3 for raw data files

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-19 | Initial package structure created |

---

**Document Control:**
- Status: READY FOR REVIEW
- Next Update: Upon completion of first validation run
