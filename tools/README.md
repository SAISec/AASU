# Tooling for AGCVCP (GitHub-backed CMDB-as-code)

This folder contains the local + CI tooling to operate the AASU Git-CMDB Version Control Protocol using GitHub pull requests.

## CLI (local developer workflow)

Validate the registry:

```bash
python3 tools/aasu_registry.py validate
```

Update AASU fingerprints after editing `spec.aasu.snapshot`:

```bash
python3 tools/aasu_registry.py fingerprint --all --write
```

Generate a relationship graph (Mermaid):

```bash
python3 tools/aasu_registry.py graph
```

Export manifests as JSON (for downstream CMDB sync tooling):

```bash
python3 tools/aasu_registry.py export --pretty --out registry-export.json
```

Generate an impact report (used in PR workflows):

```bash
python3 tools/aasu_registry.py impact --changed-files-file /tmp/changed_files.txt
```

## GitHub (recommended operational setup)

1. **Registry lives in a GitHub repo**
   - The registry is a normal Git repo; PRs are the change-control mechanism.

2. **Branch protection**
   - Protect `main`/`trunk`
   - Require PRs and require the status check from `.github/workflows/registry-validate.yml`

3. **PR impact comments (optional, but useful)**
   - `.github/workflows/registry-validate.yml` generates an “AASU Registry Impact Report” and posts/updates a PR comment marked with `<!-- aasu-registry-impact -->`.

4. **Ownership and approvals**
   - Add `CODEOWNERS` to route reviews to the owning teams for:
     - AASU snapshots (`registry/assets/aasu/**`)
     - Tools/MCP endpoints (`registry/assets/tool/**`)
     - Retrieval indices (`registry/assets/retrieval/**`)
   - Template: `.github/CODEOWNERS.template`
   - Use GitHub branch protection rules to require approvals (especially for prod-impacting paths).

5. **Evidence attachment**
   - Add links/refs to test reports and approvals in the AASU CI manifest under `spec.aasu.certification`.
