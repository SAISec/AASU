# AASU Registry (CMDB-as-code)

This folder is the **asset registry** used by the AASU Git-CMDB Version Control Protocol.

## Structure
- `registry/assets/`: Configuration Items (CIs) as YAML manifests.
- `registry/relationships/`: CI relationships as YAML manifests.
- `registry/schemas/`: JSON Schemas for validation.

## Validation
Run:

```bash
python3 tools/aasu_registry.py validate
```

## Conventions (recommended)
- Every CI gets a stable `metadata.id` (e.g., `ci:aasu:customer-support-chatbot:prod`).
- AASU snapshots MUST include a `spec.aasu.fingerprint` bound to `spec.aasu.snapshot`.
- Avoid moving references (branches) for configuration evidence; prefer commit SHAs, signed tags, digests, or provider snapshot IDs.

## Fingerprints (AASU snapshots)
When you change `spec.aasu.snapshot`, update the fingerprint:

```bash
python3 tools/aasu_registry.py fingerprint --all --write
```
