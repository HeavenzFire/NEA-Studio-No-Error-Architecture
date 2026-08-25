# Council — Archive Index
Generated: 2026-08-25T00:00:00Z (replace with actual generation time)
Generator: SOVEREIGN_ARCHIVE TOOLING (manual template)

## Purpose
- Top-level index for the /council collection: authoritative list of repositories, apps, artifacts, and representative files from Oct 15, 2024 → present.
- Each entry includes: artifact identifier, artifact type, last-known state (commit & timestamp), a SHA256 hash of the representative public tree/file, license, and a brief description.

## Index Schema (Columns)
| Field | Description |
| --- | --- |
| repo_or_artifact | owner/repo or artifact filename |
| artifact_type | repo / app / model / dataset / studio-artifact / doc / binary |
| last_commit_iso | ISO8601 timestamp of last public commit (or "last-known" event) |
| last_commit_sha | full commit SHA for the referenced state |
| sha256_hash | SHA256 of the public tree tarball or chosen canonical file |
| license | SPDX identifier or "Unknown" |
| status | archived / active / quarantined / private |
| short_description | one-line human summary |
| notes | custody/redaction flags, representative file path, provenance notes |

## How to Compute Canonical Fields

### Last Commit Timestamp & SHA
```bash
git -C /path/to/repo log -1 --format='%cI %H'
```

### Canonical SHA256 (recommended: tar of the public tree at HEAD)
```bash
git -C /path/to/repo archive --format=tar HEAD | sha256sum
```
Use this value in `sha256_hash`. For single-file artifacts:
```bash
sha256sum path/to/file | awk '{print $1}'
```

### Private Repositories
If the repo is hosted but private:
1. Produce the canonical hash from a reproducible export (tarball, zip)
2. Store the export in an encrypted WORM store
3. Put the exported artifact reference in `notes`

### Merkle Root Inclusion
Record each entry's `sha256_hash` and the path used. Use these hashes as leaves when building the DEDICATION.block Merkle root.

## Example Entries

| repo_or_artifact | artifact_type | last_commit_iso | last_commit_sha | sha256_hash | license | status | short_description | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| org/example-service | repo | 2026-06-12T14:23:08Z | ab12cd34ef56... | e3b0c44298fc1c149afbf4c8996fb924... | MIT | archived | Microservice for X | representative file: deploy/manifest.yaml |
| personal/ai-studio-artifact-001.tar.gz | studio-artifact | 2025-11-02T09:11:00Z | n/a | 9c1185a5c5e9fc54612808977ee8f548... | CC-BY-4.0 | archived | Model snapshot from AI Studio | created from export: ai-studio/export-20251102.tar.gz |
| docs/knowledge-base.pdf | doc | 2026-01-10T03:00:00Z | n/a | f96b697d7cb7938d525a2f31aaf161d0... | Unknown | archived | Consolidated knowledge base | redacted personal info in pages 12-14 |

## Recommended Minimum Metadata Per Entry (YAML Sidecar)

```yaml
---
repo_or_artifact: "org/example-service"
artifact_type: "repo"
last_commit_iso: "2026-06-12T14:23:08Z"
last_commit_sha: "ab12cd34ef56..."
sha256_hash: "e3b0c44298fc1c149afbf4c8996fb924..."
license: "MIT"
status: "archived"
short_description: "Microservice for X"
notes: "representative file: deploy/manifest.yaml; exported via git archive 2026-06-12"
---
```

## Chain-of-Custody and Signing Notes

- Keep a separate signed log (WORM) recording:
  - Who performed the export
  - UTC timestamp
  - Machine fingerprint
  - The command used
  - The resulting sha256
- Prefer detached GPG signatures for the exported tarballs
- When ready to produce the DEDICATION.block Merkle root:
  1. Gather all `sha256_hash` values from each split-index
  2. Compute a canonical leaf encoding (e.g., hex-hash + newline)
  3. Compute the Merkle root with a documented algorithm and salt (if any)
  4. Store the Merkle root and the leaf list in DEDICATION.block

## Next Steps

1. Produce `/lineage/ARCHIVE_INDEX.md` and `/public-accountability/ARCHIVE_INDEX.md` using the same schema
2. Produce `DEDICATION.block` template (Merkle root, timestamp, human dedication)
3. Produce `COC_TEMPLATE.md` (chain-of-custody WORM runbook, reproducible build checklist, public-only rules)
