# Lineage — Archive Index
Generated: 2026-08-25T00:00:00Z (replace with actual generation time)
Generator: SOVEREIGN_ARCHIVE TOOLING (manual template)

## Purpose
- Tracks the genealogy and evolution of all artifacts in the SyntropicOS ecosystem
- Records parent-child relationships between versions, forks, and derivatives
- Maintains provenance chains for auditability and attribution

## Index Schema (Columns)
| Field | Description |
| --- | --- |
| artifact_id | unique identifier for this artifact version |
| parent_artifact_id | reference to the source/parent artifact (if any) |
| artifact_type | repo / app / model / dataset / studio-artifact / doc / binary / fork / derivative |
| lineage_depth | integer depth from root origin (0 = root) |
| created_iso | ISO8601 timestamp of creation/fork |
| creator_identity | anonymized or pseudonymous creator handle |
| derivation_method | manual / auto-generated / merged / forked / distilled |
| sha256_hash | SHA256 of the canonical representation |
| license | SPDX identifier or "Unknown" |
| status | active / archived / deprecated / superseded |
| short_description | one-line summary of this version's purpose |
| change_summary | key differences from parent (if applicable) |
| notes | provenance flags, merge sources, or custody notes |

## How to Compute Lineage Fields

### Lineage Depth Calculation
```bash
# Starting from root (depth 0), increment for each derivation
# Root artifacts have lineage_depth = 0
# First-generation forks/derivatives have lineage_depth = 1
# etc.
```

### Parent Artifact Resolution
```bash
# For git-based artifacts, track the fork/branch point:
git merge-base --is-ancestor <parent-commit> <current-commit> && echo "Valid lineage"
```

### Derivation Method Classification
- `manual` — human-created from scratch
- `auto-generated` — produced by automated tooling/pipeline
- `merged` — combination of multiple parent artifacts
- `forked` — direct copy with modifications
- `distilled` — simplified/reduced version of a larger artifact

## Example Entries

| artifact_id | parent_artifact_id | artifact_type | lineage_depth | created_iso | creator_identity | derivation_method | sha256_hash | license | status | short_description | change_summary | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| syntropic-core-v0.1 | null | repo | 0 | 2024-10-15T00:00:00Z | architect-alpha | manual | a1b2c3d4... | MIT | archived | Original SyntropicOS core | initial release | root artifact |
| syntropic-core-v0.2 | syntropic-core-v0.1 | repo | 1 | 2025-01-20T12:00:00Z | architect-alpha | manual | e5f6g7h8... | MIT | active | Enhanced core with 144Hz sync | added frequency lock module | performance optimization |
| council-archive-tool | syntropic-core-v0.2 | app | 1 | 2025-06-10T08:30:00Z | builder-beta | forked | i9j0k1l2... | Apache-2.0 | active | Archive indexing utility | extracted archive module | standalone deployment |
| merged-pipeline-v1 | [council-archive-tool, telemetry-module] | app | 2 | 2026-02-15T16:45:00Z | integrator-gamma | merged | m3n4o5p6... | MIT | active | Unified pipeline orchestrator | combined archive + telemetry | multi-parent merge |

## Recommended Minimum Metadata Per Entry (YAML Sidecar)

```yaml
---
artifact_id: "syntropic-core-v0.2"
parent_artifact_id: "syntropic-core-v0.1"
artifact_type: "repo"
lineage_depth: 1
created_iso: "2025-01-20T12:00:00Z"
creator_identity: "architect-alpha"
derivation_method: "manual"
sha256_hash: "e5f6g7h8..."
license: "MIT"
status: "active"
short_description: "Enhanced core with 144Hz sync"
change_summary: "added frequency lock module"
notes: "performance optimization; backward compatible with v0.1"
---
```

## Lineage Visualization Commands

### Generate Lineage Tree (GraphViz format)
```bash
# Export lineage data to DOT format for visualization
cat << 'EOF' > lineage.dot
digraph Lineage {
    rankdir=TB;
    "syntropic-core-v0.1" -> "syntropic-core-v0.2";
    "syntropic-core-v0.2" -> "council-archive-tool";
    "syntropic-core-v0.2" -> "telemetry-module";
    "council-archive-tool" -> "merged-pipeline-v1";
    "telemetry-module" -> "merged-pipeline-v1";
}
EOF
dot -Tpng lineage.dot -o lineage_tree.png
```

### Query Lineage Chain
```bash
# Trace full ancestry of an artifact
trace_ancestry() {
    local artifact="$1"
    while [[ -n "$artifact" && "$artifact" != "null" ]]; do
        echo "$artifact"
        artifact=$(grep "^$artifact|" lineage_index.csv | cut -d'|' -f2)
    done
}
```

## Integration with DEDICATION.block

Each lineage entry's `sha256_hash` should be included as a leaf in the Merkle tree when computing the DEDICATION.block root. The `artifact_id` serves as the canonical path identifier for each leaf.

## Next Steps

1. Populate with actual artifact lineage data from the SyntropicOS ecosystem
2. Cross-reference entries with `/council/ARCHIVE_INDEX.md` for consistency
3. Generate visual lineage graph for documentation
4. Include lineage hashes in DEDICATION.block Merkle root computation
