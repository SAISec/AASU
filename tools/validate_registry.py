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


def _asset_type(obj: dict[str, Any]) -> str | None:
    spec = obj.get("spec")
    if not isinstance(spec, dict):
        return None
    typ = spec.get("type")
    return typ if isinstance(typ, str) else None


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
    assets_obj_by_id: dict[str, dict[str, Any]] = {}
    rels_by_id: dict[str, Path] = {}
    relationships: list[tuple[Path, dict[str, Any]]] = []
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
                    assets_obj_by_id[ci_id] = obj

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
            relationships.append((path, obj))

    relationship_types_expected: dict[str, tuple[set[str], set[str]]] = {
        "uses_short_term_memory": ({"aasu"}, {"memory_short_term_profile"}),
        "uses_long_term_memory": ({"aasu"}, {"memory_long_term_profile"}),
        "uses_skill": ({"aasu"}, {"skill_package"}),
        "uses_knowledge_graph": ({"aasu"}, {"knowledge_graph"}),
        "uses_context_graph_profile": ({"aasu"}, {"context_graph_profile"}),
        "context_graph_derived_from": ({"context_graph_profile"}, {"knowledge_graph"}),
        "stores_memory_in": (
            {"memory_short_term_profile", "memory_long_term_profile"},
            {"store"},
        ),
        "indexes_from_corpus": ({"retrieval"}, {"dataset"}),
        "attests": ({"attestation_bundle", "aibom_document"}, set()),
    }

    outgoing_by_from: dict[str, list[tuple[str, str, Path]]] = {}
    for path, obj in relationships:
        spec = obj.get("spec") or {}
        from_id = spec.get("from")
        to_id = spec.get("to")
        rel_type = spec.get("type")
        if isinstance(from_id, str) and from_id not in assets_by_id:
            had_errors = True
            error(f"Relationship endpoint missing (from='{from_id}') referenced by {path}")
        if isinstance(to_id, str) and to_id not in assets_by_id:
            had_errors = True
            error(f"Relationship endpoint missing (to='{to_id}') referenced by {path}")

        if not (isinstance(from_id, str) and isinstance(to_id, str) and isinstance(rel_type, str)):
            continue

        outgoing_by_from.setdefault(from_id, []).append((rel_type, to_id, path))

        expected = relationship_types_expected.get(rel_type)
        if expected is None:
            continue

        from_types, to_types = expected
        from_obj = assets_obj_by_id.get(from_id)
        to_obj = assets_obj_by_id.get(to_id)
        from_type = _asset_type(from_obj) if isinstance(from_obj, dict) else None
        to_type = _asset_type(to_obj) if isinstance(to_obj, dict) else None

        if from_types and from_type not in from_types:
            had_errors = True
            error(
                f"Relationship type '{rel_type}' requires from.type in {sorted(from_types)}, "
                f"got '{from_type}' for {from_id} in {path}"
            )
        if to_types and to_type not in to_types:
            had_errors = True
            error(
                f"Relationship type '{rel_type}' requires to.type in {sorted(to_types)}, "
                f"got '{to_type}' for {to_id} in {path}"
            )

    for ci_id, ci_obj in assets_obj_by_id.items():
        if _asset_type(ci_obj) != "aasu":
            continue
        spec = ci_obj.get("spec") or {}
        environment = spec.get("environment")
        outgoing = outgoing_by_from.get(ci_id, [])

        stm = [r for r in outgoing if r[0] == "uses_short_term_memory"]
        if len(stm) > 1:
            had_errors = True
            error(
                f"AASU '{ci_id}' has multiple uses_short_term_memory relationships ({len(stm)})."
            )

        ltm = [r for r in outgoing if r[0] == "uses_long_term_memory"]
        if len(ltm) > 1:
            had_errors = True
            error(
                f"AASU '{ci_id}' has multiple uses_long_term_memory relationships ({len(ltm)})."
            )
        if ltm and not stm:
            had_errors = True
            error(
                f"AASU '{ci_id}' uses long-term memory but is missing uses_short_term_memory relationship."
            )
        if environment == "prod" and stm and len(ltm) != 1:
            had_errors = True
            error(
                f"Production AASU '{ci_id}' with memory enabled must have exactly one "
                f"uses_long_term_memory relationship; found {len(ltm)}"
            )

        kg = [r for r in outgoing if r[0] == "uses_knowledge_graph"]
        cg = [r for r in outgoing if r[0] == "uses_context_graph_profile"]
        if cg and not kg:
            had_errors = True
            error(
                f"AASU '{ci_id}' uses_context_graph_profile but has no uses_knowledge_graph relationship."
            )

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
