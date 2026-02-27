#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_DIR = REPO_ROOT / "registry"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_sha256_fingerprint(snapshot: Any) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(snapshot)).hexdigest()
    return f"sha256:{digest}"


def load_yaml_file(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surface context in error output
        raise ValueError(f"Failed to parse YAML: {path}: {exc}") from exc


def iter_manifest_files(registry_dir: Path) -> Iterable[Path]:
    for folder in ("assets", "relationships"):
        base = registry_dir / folder
        if not base.exists():
            continue
        yield from sorted(base.rglob("*.y*ml"))


def load_schema(path: Path) -> Draft202012Validator:
    schema_obj = json.loads(path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema_obj)


def error(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def validate_registry_dir(registry_dir: Path) -> int:
    registry_dir = registry_dir.resolve()
    schemas_dir = registry_dir / "schemas"

    ci_schema_path = schemas_dir / "configuration-item.schema.json"
    rel_schema_path = schemas_dir / "relationship.schema.json"

    if not ci_schema_path.exists():
        error(f"Missing schema: {ci_schema_path}")
        return 2
    if not rel_schema_path.exists():
        error(f"Missing schema: {rel_schema_path}")
        return 2

    ci_validator = load_schema(ci_schema_path)
    rel_validator = load_schema(rel_schema_path)

    manifests: list[tuple[Path, Any]] = []
    for path in iter_manifest_files(registry_dir):
        obj = load_yaml_file(path)
        if not isinstance(obj, dict):
            error(f"Manifest must be a YAML mapping/object: {path}")
            return 2
        manifests.append((path, obj))

    assets_by_id: dict[str, Path] = {}
    rels_by_id: dict[str, Path] = {}
    had_errors = False

    for path, obj in manifests:
        kind = obj.get("kind")
        if kind == "ConfigurationItem":
            validator = ci_validator
        elif kind == "Relationship":
            validator = rel_validator
        else:
            error(f"Unknown kind (expected ConfigurationItem/Relationship): {path}")
            had_errors = True
            continue

        for err in validator.iter_errors(obj):
            had_errors = True
            loc = "/".join(str(p) for p in err.absolute_path)
            error(f"Schema violation in {path} at '{loc}': {err.message}")

        if kind == "ConfigurationItem":
            ci_id = (obj.get("metadata") or {}).get("id")
            if isinstance(ci_id, str):
                if ci_id in assets_by_id:
                    had_errors = True
                    error(f"Duplicate CI id '{ci_id}' in {path} (already in {assets_by_id[ci_id]})")
                else:
                    assets_by_id[ci_id] = path

            spec = obj.get("spec") or {}
            if spec.get("type") == "aasu":
                aasu = spec.get("aasu") or {}
                snapshot = aasu.get("snapshot")
                fp = aasu.get("fingerprint") or {}
                fp_value = fp.get("value")
                if snapshot is None:
                    had_errors = True
                    error(f"Missing spec.aasu.snapshot in {path}")
                else:
                    expected = compute_sha256_fingerprint(snapshot)
                    if fp_value != expected:
                        had_errors = True
                        error(
                            "AASU fingerprint mismatch in "
                            f"{path}: expected '{expected}', got '{fp_value}'"
                        )

        if kind == "Relationship":
            rel_id = (obj.get("metadata") or {}).get("id")
            if isinstance(rel_id, str):
                if rel_id in rels_by_id:
                    had_errors = True
                    error(f"Duplicate relationship id '{rel_id}' in {path} (already in {rels_by_id[rel_id]})")
                else:
                    rels_by_id[rel_id] = path

    for path, obj in manifests:
        if obj.get("kind") != "Relationship":
            continue
        spec = obj.get("spec") or {}
        from_id = spec.get("from")
        to_id = spec.get("to")
        if isinstance(from_id, str) and from_id not in assets_by_id:
            had_errors = True
            error(f"Relationship endpoint missing (from='{from_id}') referenced by {path}")
        if isinstance(to_id, str) and to_id not in assets_by_id:
            had_errors = True
            error(f"Relationship endpoint missing (to='{to_id}') referenced by {path}")

    if had_errors:
        return 1

    print(f"OK: validated {len(assets_by_id)} assets and {len(rels_by_id)} relationships.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AASU registry manifests (CMDB-as-code).")
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY_DIR),
        help="Path to registry directory (default: ./registry)",
    )
    args = parser.parse_args()
    return validate_registry_dir(Path(args.registry))


if __name__ == "__main__":
    raise SystemExit(main())
