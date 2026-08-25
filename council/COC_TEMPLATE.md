# Chain-of-Custody (CoC) Template — SyntropicOS Sovereign Archive

## Document Metadata
```
DOCUMENT_VERSION: 1.0
DOCUMENT_TYPE: CHAIN_OF_CUSTODY_RUNBOOK
GENERATION_TIMESTAMP: 2026-08-25T00:00:00Z
APPLICABLE_SYSTEMS: SyntropicOS Multi-Module Orchestration Pipeline
TARGET_NODE: DESKTOP-0142RR5
FREQUENCY_LOCK: 144Hz
```

## Purpose and Scope

This document establishes the authoritative chain-of-custody (CoC) procedures for all
artifacts within the SyntropicOS sovereign archive system. It defines:

1. **Export Procedures**: How to reproducibly extract artifacts from source systems
2. **Hashing Protocols**: Canonical methods for computing integrity checksums
3. **Signing Requirements**: Cryptographic attestation of custody transfers
4. **Storage Standards**: WORM (Write-Once-Read-Many) preservation guidelines
5. **Audit Trails**: Logging requirements for accountability verification
6. **Public-Only Rules**: Restrictions on what may be included in public indexes

## Section 1: Reproducible Build Checklist

### Pre-Export Verification
- [ ] Source repository/artifact is accessible and in known-good state
- [ ] Export environment is clean (no uncommitted local modifications)
- [ ] System clock is synchronized (NTP verified)
- [ ] Export tooling versions are documented
- [ ] Target storage location is prepared and writable

### Export Commands (by Artifact Type)

#### Git Repository
```bash
REPO_PATH="/path/to/repo"
EXPORT_DIR="$HOME/.syntropic_workspace/payloads/exports"
mkdir -p "$EXPORT_DIR"

# Compute canonical hash
HASH=$(git -C "$REPO_PATH" archive --format=tar HEAD | sha256sum | awk '{print $1}')

# Create timestamped export
TIMESTAMP=$(date -u +'%Y%m%d_%H%M%S')
ARTIFACT_NAME=$(basename "$REPO_PATH")
git -C "$REPO_PATH" archive --format=tar.gz HEAD > "$EXPORT_DIR/${ARTIFACT_NAME}_${TIMESTAMP}.tar.gz"

# Record metadata
echo "ARTIFACT: ${ARTIFACT_NAME}" >> "$EXPORT_DIR/coc_log.txt"
echo "TIMESTAMP: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> "$EXPORT_DIR/coc_log.txt"
echo "OPERATOR: $(whoami)" >> "$EXPORT_DIR/coc_log.txt"
echo "MACHINE: $(hostname)" >> "$EXPORT_DIR/coc_log.txt"
echo "SOURCE_COMMIT: $(git -C "$REPO_PATH" log -1 --format='%H')" >> "$EXPORT_DIR/coc_log.txt"
echo "SHA256_HASH: $HASH" >> "$EXPORT_DIR/coc_log.txt"
echo "---" >> "$EXPORT_DIR/coc_log.txt"
```

#### Single File Artifact
```bash
FILE_PATH="/path/to/file"
HASH=$(sha256sum "$FILE_PATH" | awk '{print $1}')
TIMESTAMP=$(date -u +'%Y%m%d_%H%M%S')
BASENAME=$(basename "$FILE_PATH")

# Copy to export directory with timestamp
cp "$FILE_PATH" "$EXPORT_DIR/${BASENAME%.${BASENAME##*.}}_${TIMESTAMP}.${BASENAME##*.}"

# Log custody transfer
echo "ARTIFACT: $BASENAME" >> "$EXPORT_DIR/coc_log.txt"
echo "TIMESTAMP: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> "$EXPORT_DIR/coc_log.txt"
echo "OPERATOR: $(whoami)" >> "$EXPORT_DIR/coc_log.txt"
echo "MACHINE: $(hostname)" >> "$EXPORT_DIR/coc_log.txt"
echo "SOURCE_PATH: $FILE_PATH" >> "$EXPORT_DIR/coc_log.txt"
echo "SHA256_HASH: $HASH" >> "$EXPORT_DIR/coc_log.txt"
echo "---" >> "$EXPORT_DIR/coc_log.txt"
```

#### Binary/Compiled Artifact
```bash
BINARY_PATH="/path/to/binary"
HASH=$(sha256sum "$BINARY_PATH" | awk '{print $1}')
TIMESTAMP=$(date -u +'%Y%m%d_%H%M%S')
BASENAME=$(basename "$BINARY_PATH")

# Verify binary is not corrupted (optional: run integrity tests)
# file "$BINARY_PATH"
# ldd "$BINARY_PATH"  # Check dependencies if applicable

# Export with metadata
cp "$BINARY_PATH" "$EXPORT_DIR/${BASENAME%.${BASENAME##*.}}_${TIMESTAMP}.${BASENAME##*.}"

echo "ARTIFACT: $BASENAME" >> "$EXPORT_DIR/coc_log.txt"
echo "TIMESTAMP: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> "$EXPORT_DIR/coc_log.txt"
echo "OPERATOR: $(whoami)" >> "$EXPORT_DIR/coc_log.txt"
echo "MACHINE: $(hostname)" >> "$EXPORT_DIR/coc_log.txt"
echo "SOURCE_PATH: $BINARY_PATH" >> "$EXPORT_DIR/coc_log.txt"
echo "SHA256_HASH: $HASH" >> "$EXPORT_DIR/coc_log.txt"
echo "ARTIFACT_TYPE: binary" >> "$EXPORT_DIR/coc_log.txt"
echo "---" >> "$EXPORT_DIR/coc_log.txt"
```

## Section 2: Cryptographic Signing Protocol

### GPG Signature Generation
```bash
# Generate detached signature for exported artifact
gpg --armor --detach-sign "$EXPORT_DIR/artifact_name.tar.gz"

# Verify signature
gpg --verify "$EXPORT_DIR/artifact_name.tar.gz.sig" "$EXPORT_DIR/artifact_name.tar.gz"
```

### Key Management Requirements
- Use dedicated signing key (separate from daily-use keys)
- Key strength: minimum 4096-bit RSA or Ed25519
- Key storage: hardware security module (HSM) or air-gapped system preferred
- Key rotation: annual, with overlapping validity period for verification

### Signature Verification for Public Releases
```bash
# Import SyntropicOS public key
gpg --import syntropic-archive-public.key

# Verify any released artifact
gpg --verify <artifact>.sig <artifact>
```

## Section 3: WORM Storage Implementation

### Local WORM Simulation
```bash
# Create append-only log directory
LOG_DIR="$HOME/.syntropic_workspace/logs/coc_worm"
mkdir -p "$LOG_DIR"
chattr +a "$LOG_DIR"  # Linux: set append-only attribute

# Append custody record
echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') | $OPERATOR | $ACTION | $ARTIFACT | $HASH" >> "$LOG_DIR/custody.log"
```

### Cloud WORM Storage (AWS S3 Object Lock)
```bash
# Enable Object Lock on bucket (must be done at creation)
aws s3api create-bucket \
  --bucket syntropic-archive-worm \
  --object-lock-enabled

# Set retention policy on uploaded object
aws s3api put-object-retention \
  --bucket syntropic-archive-worm \
  --key "coc/custody_log_$(date +%Y%m%d).txt" \
  --retention '{"Mode": "GOVERNANCE", "RetainUntilDate": "2036-08-25T00:00:00Z"}'
```

### IPFS Distributed Storage
```bash
# Add CoC record to IPFS
ipfs add --pin=true custody_log.txt
# Record the returned CID for future retrieval and verification
```

## Section 4: Audit Trail Requirements

### Minimum Log Entry Fields
Every custody transfer must record:
1. **Timestamp**: ISO8601 UTC format
2. **Operator Identity**: Username or pseudonymous handle
3. **Machine Fingerprint**: Hostname, hardware ID, or container ID
4. **Action Performed**: export / hash / sign / transfer / verify
5. **Artifact Identifier**: Name, path, or unique ID
6. **Hash Value**: SHA256 of artifact at time of action
7. **Command Executed**: Exact command line used (for reproducibility)

### Log Integrity Verification
```bash
# Generate hash chain for log file
sha256sum custody_log.txt > custody_log.txt.sha256

# For enhanced integrity, create hash chain where each entry includes previous hash
# This prevents insertion attacks
```

### Quarterly Audit Procedure
1. Retrieve all CoC logs from WORM storage
2. Verify hash chain integrity
3. Cross-reference with DEDICATION.block commitments
4. Document any discrepancies or anomalies
5. Publish audit summary to public accountability registry

## Section 5: Public-Only Rules

### What MAY Be Included in Public Indexes
- Artifacts under OSI-approved open source licenses
- Artifacts under Creative Commons licenses (CC-BY, CC-BY-SA, CC0)
- Documentation and educational materials
- Publicly released binaries with clear provenance
- Hash commitments and Merkle root data

### What MUST NOT Be Included in Public Indexes
- Private or proprietary code without explicit permission
- Personal identifying information (PII)
- API keys, credentials, or secrets (even accidentally committed)
- Internal-only documentation marked confidential
- Third-party artifacts without redistribution rights
- Security-sensitive configurations or infrastructure details

### Redaction Protocol
If an artifact contains sensitive material:
1. Create redacted version with sensitive portions removed
2. Document redaction in `notes` field of archive index
3. Store original in encrypted private archive (not public index)
4. Use redacted version's hash for public DEDICATION.block commitment

Example notes field for redacted artifact:
```
notes: "Pages 12-14 redacted (contained internal API endpoints); 
        original stored in encrypted private archive PA-2026-001"
```

## Section 6: Integration with DEDICATION.block

### Referencing CoC Records in DEDICATION.block
Each artifact in the DEDICATION.block leaf list should have a corresponding CoC record:

```
LEAF_NNN | artifact_name | sha256_hash | /council/ARCHIVE_INDEX.md | CoC_REF:coc_log_20260825.txt:line_MMM
```

### Verification Workflow
1. Retrieve artifact from archive
2. Compute SHA256 hash
3. Compare with DEDICATION.block commitment
4. Locate CoC record using CoC_REF
5. Verify CoC log entry matches artifact metadata
6. Confirm GPG signature (if signed release)
7. Validate operator authorization for that custody transfer

## Section 7: Emergency Procedures

### Compromised Key Protocol
If a signing key is suspected compromised:
1. Immediately revoke key and publish revocation certificate
2. Generate new signing key
3. Re-sign all active artifacts with new key
4. Publish security advisory with timeline and affected artifacts
5. Update DEDICATION.block with new signature commitments

### Lost Artifact Recovery
If an archived artifact is lost or corrupted:
1. Attempt recovery from distributed replicas (IPFS, mirror nodes)
2. If unrecoverable, document loss in public accountability registry
3. Remove from active DEDICATION.block (maintain historical record)
4. Initiate rebuild from source if possible
5. Create new CoC record for recovered/rebuilt artifact

### Integrity Failure Response
If hash mismatch detected between artifact and DEDICATION.block:
1. Quarantine affected artifact immediately
2. Flag entry in public accountability registry
3. Investigate source of discrepancy (corruption vs. tampering)
4. Notify stakeholders via security channel
5. Publish findings and remediation steps

## Appendix A: Command Quick Reference

```bash
# Export git repo with hash
git -C /path/to/repo archive --format=tar HEAD | tee >(sha256sum) | gzip > export.tar.gz

# Sign export
gpg --armor --detach-sign export.tar.gz

# Verify signature
gpg --verify export.tar.gz.sig export.tar.gz

# Compute hash for verification
sha256sum export.tar.gz

# Append to WORM log
echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') | $USER | export | my-artifact | $(sha256sum export.tar.gz | awk '{print $1}')" >> /worm/custody.log

# Verify against DEDICATION.block
grep "my-artifact" DEDICATION.block
```

## Appendix B: Template Custody Log Entry

```
================================================================================
CUSTODY TRANSFER RECORD
================================================================================
TIMESTAMP:     2026-08-25T12:34:56Z
OPERATOR:      architect-alpha
MACHINE:       DESKTOP-0142RR5
ACTION:        export_and_sign
ARTIFACT:      syntropic-core-v0.2.tar.gz
SOURCE:        git@github.com:syntropic/core.git @ ab12cd34ef56...
SHA256_HASH:   e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6...
SIGNATURE:     syntropic-archive-2026.key (RSA 4096)
STORAGE_LOC:   s3://syntropic-archive-worm/exports/2026/08/
NOTES:         Standard quarterly export; no anomalies detected
VERIFIED_BY:   automated_integrity_check_v1.2
================================================================================
```

---

**Document Status**: ACTIVE  
**Last Reviewed**: 2026-08-25T00:00:00Z  
**Next Review**: Quarterly or upon procedural change  
**Maintained By**: SyntropicOS Archive Governance Council
