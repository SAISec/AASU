---
layout: default
title: Registry and Tooling
---

# Registry and tooling

The registry is a **CMDB-as-code** representation of AI Configuration Items (CIs) and their relationships.

## Core workflows

Validate all manifests (schemas + relationship integrity + AASU fingerprint checks):

```bash
python3 tools/aasu_registry.py validate
```

Run regulated policy checks (pinning, memory links, attestation linkage):

```bash
python3 tools/aasu_registry.py policy-check
```

After editing an AASU snapshot `(P,M,R,T,K)`, update fingerprints and re-validate:

```bash
python3 tools/aasu_registry.py fingerprint --all --write
python3 tools/aasu_registry.py validate
```

Generate an impact report (used by PR workflows):

```bash
python3 tools/aasu_registry.py impact --changed-files-file /tmp/changed_files.txt
```

Render the relationship graph as Mermaid:

```bash
python3 tools/aasu_registry.py graph
```

Export registry manifests as JSON (for CMDB sync tooling):

```bash
python3 tools/aasu_registry.py export --pretty --out registry-export.json
```

Audit short-term and long-term memory coverage:

```bash
python3 tools/aasu_registry.py memory-audit --strict
```

Verify attestation relationships:

```bash
python3 tools/aasu_registry.py attest-verify
```

## GitHub PR workflow (recommended)
- Require the validation workflow: `.github/workflows/registry-validate.yml`
- Optionally post an “Impact Report” PR comment (already configured in the workflow)
- Use `.github/CODEOWNERS.template` (rename/customize) + branch protections for required approvals
