#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    from tools.validate_registry import (  # type: ignore[import-not-found]
        DEFAULT_REGISTRY_DIR,
        compute_sha256_fingerprint,
        iter_manifest_files,
        load_yaml_file,
        validate_registry_dir,
    )
except ModuleNotFoundError:
    # Support running as a script: `python3 tools/aasu_registry.py ...`
    from validate_registry import (  # type: ignore[import-not-found]
        DEFAULT_REGISTRY_DIR,
        compute_sha256_fingerprint,
        iter_manifest_files,
        load_yaml_file,
        validate_registry_dir,
    )


def error(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def _dump_json(value: Any, *, pretty: bool) -> str:
    if pretty:
        return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def iter_manifests(registry_dir: Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    for path in iter_manifest_files(registry_dir):
        obj = load_yaml_file(path)
        if not isinstance(obj, dict):
            raise ValueError(f"Manifest must be a YAML mapping/object: {path}")
        yield (path, obj)


def _is_aasu_ci(obj: dict[str, Any]) -> bool:
    if obj.get("kind") != "ConfigurationItem":
        return False
    spec = obj.get("spec") or {}
    return spec.get("type") == "aasu"


def _read_nested(obj: dict[str, Any], path: list[str]) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _ci_type(obj: dict[str, Any]) -> str | None:
    spec = obj.get("spec")
    if not isinstance(spec, dict):
        return None
    typ = spec.get("type")
    return typ if isinstance(typ, str) else None


def _is_prod_aasu(obj: dict[str, Any]) -> bool:
    if _ci_type(obj) != "aasu":
        return False
    spec = obj.get("spec")
    if not isinstance(spec, dict):
        return False
    return spec.get("environment") == "prod"


def _is_unpinned_version(version: str) -> bool:
    value = version.strip().lower()
    return value in {"provider:rolling", "latest", "main", "master"}


def _load_assets_and_relationships(
    registry_dir: Path,
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, str]]]:
    assets_by_id: dict[str, dict[str, Any]] = {}
    relationships: list[tuple[str, str, str]] = []

    for _, obj in iter_manifests(registry_dir):
        kind = obj.get("kind")
        if kind == "ConfigurationItem":
            ci_id = _read_nested(obj, ["metadata", "id"])
            if isinstance(ci_id, str):
                assets_by_id[ci_id] = obj
            continue

        if kind == "Relationship":
            rel_type = _read_nested(obj, ["spec", "type"])
            from_id = _read_nested(obj, ["spec", "from"])
            to_id = _read_nested(obj, ["spec", "to"])
            if isinstance(rel_type, str) and isinstance(from_id, str) and isinstance(to_id, str):
                relationships.append((rel_type, from_id, to_id))

    return assets_by_id, relationships


def _replace_single_occurrence(text: str, old: str, new: str) -> str | None:
    if old == new:
        return text
    count = text.count(old)
    if count != 1:
        return None
    return text.replace(old, new, 1)


def update_aasu_fingerprint_in_file(path: Path, *, write: bool) -> tuple[bool, str | None]:
    """
    Returns: (changed, expected_fingerprint)
    - changed=False means already correct (or only checked).
    - changed=True means file was updated (only when write=True).
    """
    obj = load_yaml_file(path)
    if not isinstance(obj, dict):
        raise ValueError(f"Manifest must be a YAML mapping/object: {path}")

    if not _is_aasu_ci(obj):
        raise ValueError(f"Not an AASU ConfigurationItem manifest: {path}")

    snapshot = _read_nested(obj, ["spec", "aasu", "snapshot"])
    if snapshot is None:
        raise ValueError(f"Missing spec.aasu.snapshot: {path}")

    expected = compute_sha256_fingerprint(snapshot)

    existing = _read_nested(obj, ["spec", "aasu", "fingerprint", "value"])
    if not isinstance(existing, str):
        raise ValueError(f"Missing/invalid spec.aasu.fingerprint.value: {path}")

    if existing == expected:
        return (False, expected)

    if not write:
        return (False, expected)

    original_text = path.read_text(encoding="utf-8")
    patched = _replace_single_occurrence(original_text, existing, expected)
    if patched is None:
        # Fallback: surgical line replacement for "value: <fingerprint>"
        # Only updates the first matching fingerprint-like line.
        pattern = re.compile(r"^(\s*value:\s*)(sha256:[a-f0-9]{64})(\s*)$", re.MULTILINE)

        def _sub(match: re.Match[str]) -> str:
            return f"{match.group(1)}{expected}{match.group(3)}"

        patched2, n = pattern.subn(_sub, original_text, count=1)
        if n != 1:
            raise ValueError(
                f"Could not safely patch fingerprint in-place (expected '{existing}' -> '{expected}'): {path}"
            )
        patched = patched2

    path.write_text(patched, encoding="utf-8")
    return (True, expected)


def cmd_validate(args: argparse.Namespace) -> int:
    return validate_registry_dir(Path(args.registry))


def cmd_fingerprint(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()
    targets: list[Path] = []

    if args.file:
        targets = [Path(args.file).resolve()]
    elif args.all:
        for path, obj in iter_manifests(registry_dir):
            if _is_aasu_ci(obj):
                targets.append(path)
    else:
        error("Select targets via --file or --all.")
        return 2

    had_mismatch = False
    changed_any = False
    for path in targets:
        try:
            obj = load_yaml_file(path)
            if not isinstance(obj, dict):
                raise ValueError("Manifest must be a YAML mapping/object")
            if not _is_aasu_ci(obj):
                error(f"Skipping non-AASU manifest: {path}")
                had_mismatch = True
                continue

            existing = _read_nested(obj, ["spec", "aasu", "fingerprint", "value"])
            snapshot = _read_nested(obj, ["spec", "aasu", "snapshot"])
            expected = compute_sha256_fingerprint(snapshot)

            if existing != expected:
                had_mismatch = True
                if args.write:
                    changed, _ = update_aasu_fingerprint_in_file(path, write=True)
                    changed_any = changed_any or changed
                    print(f"UPDATED: {path} -> {expected}")
                else:
                    print(f"MISMATCH: {path} expected {expected} got {existing}")
            else:
                print(f"OK: {path}")
        except Exception as exc:  # noqa: BLE001
            error(f"{path}: {exc}")
            return 2

    if args.write and changed_any:
        # After updating, re-validate to keep the workflow tight.
        return validate_registry_dir(registry_dir)

    return 1 if had_mismatch else 0


def cmd_export(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()

    assets: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    for path, obj in iter_manifests(registry_dir):
        kind = obj.get("kind")
        if kind == "ConfigurationItem":
            assets.append({"path": str(path.relative_to(registry_dir.parent)), "manifest": obj})
        elif kind == "Relationship":
            relationships.append({"path": str(path.relative_to(registry_dir.parent)), "manifest": obj})

    payload = {
        "registry": str(registry_dir),
        "assets": assets,
        "relationships": relationships,
    }

    out_text = _dump_json(payload, pretty=args.pretty)
    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")
        print(f"WROTE: {args.out}")
        return 0

    sys.stdout.write(out_text)
    return 0


def _mermaid_node_id(ci_id: str) -> str:
    # Mermaid node identifiers must be simple; keep the display label as the original CI ID.
    return re.sub(r"[^a-zA-Z0-9_]", "_", ci_id)


def cmd_graph(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()

    assets_by_id: dict[str, dict[str, Any]] = {}
    rels: list[dict[str, Any]] = []

    for _, obj in iter_manifests(registry_dir):
        kind = obj.get("kind")
        if kind == "ConfigurationItem":
            ci_id = _read_nested(obj, ["metadata", "id"])
            if isinstance(ci_id, str):
                assets_by_id[ci_id] = obj
        elif kind == "Relationship":
            rels.append(obj)

    if args.format != "mermaid":
        error(f"Unsupported graph format: {args.format}")
        return 2

    lines: list[str] = ["flowchart LR"]
    declared: set[str] = set()

    def declare(ci_id: str) -> None:
        if ci_id in declared:
            return
        node_id = _mermaid_node_id(ci_id)
        lines.append(f'  {node_id}["{ci_id}"]')
        declared.add(ci_id)

    for rel in rels:
        spec = rel.get("spec") or {}
        rel_type = spec.get("type")
        from_id = spec.get("from")
        to_id = spec.get("to")
        if not (isinstance(from_id, str) and isinstance(to_id, str)):
            continue
        declare(from_id)
        declare(to_id)
        from_node = _mermaid_node_id(from_id)
        to_node = _mermaid_node_id(to_id)
        label = rel_type if isinstance(rel_type, str) else "rel"
        lines.append(f"  {from_node} -->|{label}| {to_node}")

    out = "```mermaid\n" + "\n".join(lines) + "\n```\n"
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"WROTE: {args.out}")
        return 0

    sys.stdout.write(out)
    return 0


def _read_changed_files_from_json(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict) and isinstance(raw.get("files"), list):
        return [item for item in raw["files"] if isinstance(item, dict)]
    raise ValueError("Expected a JSON list of objects or an object with a 'files' array.")


def _read_changed_files_from_lines(path: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        files.append({"filename": line, "status": "modified"})
    return files


def _normalize_changed_file_entry(entry: dict[str, Any]) -> dict[str, Any]:
    filename = entry.get("filename") or entry.get("path")
    if not isinstance(filename, str) or not filename:
        raise ValueError("Changed file entry missing 'filename'.")
    status = entry.get("status")
    if not isinstance(status, str) or not status:
        status = "modified"
    prev = entry.get("previous_filename")
    if prev is not None and not isinstance(prev, str):
        prev = None
    return {"filename": filename, "status": status, "previous_filename": prev}


def _load_registry_index(registry_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    """
    Returns:
    - assets_by_id: CI id -> manifest dict
    - aasu_reverse_refs: asset CI id -> set of AASU CI ids that reference it in (P,M,R,T,K)
    """
    assets_by_id, relationships = _load_assets_and_relationships(registry_dir)
    aasu_reverse_refs: dict[str, set[str]] = defaultdict(set)

    for ci_id, obj in assets_by_id.items():
        spec = obj.get("spec") or {}
        if spec.get("type") != "aasu":
            continue
        snapshot = _read_nested(obj, ["spec", "aasu", "snapshot"])
        if not isinstance(snapshot, dict):
            continue

        def add_ref(component: Any) -> None:
            if not isinstance(component, dict):
                return
            ref_id = component.get("asset")
            if isinstance(ref_id, str):
                aasu_reverse_refs[ref_id].add(ci_id)

        for key in ("P", "M", "R", "K"):
            add_ref(snapshot.get(key))
        tools = snapshot.get("T")
        if isinstance(tools, list):
            for t in tools:
                add_ref(t)

    outgoing: dict[str, set[str]] = defaultdict(set)
    for _, from_id, to_id in relationships:
        outgoing[from_id].add(to_id)

    for ci_id, obj in assets_by_id.items():
        if _ci_type(obj) != "aasu":
            continue
        visited: set[str] = set()
        stack = list(outgoing.get(ci_id, set()))
        while stack:
            nxt = stack.pop()
            if nxt in visited:
                continue
            visited.add(nxt)
            aasu_reverse_refs[nxt].add(ci_id)
            for child in outgoing.get(nxt, set()):
                if child not in visited:
                    stack.append(child)

    return assets_by_id, aasu_reverse_refs


def _format_owner_list(owners: Any) -> list[str]:
    if not isinstance(owners, list):
        return []
    out: list[str] = []
    for o in owners:
        if not isinstance(o, dict):
            continue
        otype = o.get("type")
        oid = o.get("id")
        role = o.get("role")
        if isinstance(otype, str) and isinstance(oid, str) and isinstance(role, str):
            out.append(f"{otype}:{oid} ({role})")
    return out


def _index_relationships(
    relationships: list[tuple[str, str, str]],
) -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[tuple[str, str]]]]:
    outgoing: dict[str, list[tuple[str, str]]] = defaultdict(list)
    incoming: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rel_type, from_id, to_id in relationships:
        outgoing[from_id].append((rel_type, to_id))
        incoming[to_id].append((rel_type, from_id))
    return outgoing, incoming


def cmd_policy_check(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()
    if not args.skip_validate:
        base_rc = validate_registry_dir(registry_dir)
        if base_rc != 0:
            return base_rc

    assets_by_id, relationships = _load_assets_and_relationships(registry_dir)
    outgoing, incoming = _index_relationships(relationships)

    findings: list[str] = []
    for ci_id, obj in assets_by_id.items():
        if not _is_prod_aasu(obj):
            continue

        snapshot = _read_nested(obj, ["spec", "aasu", "snapshot"])
        if not isinstance(snapshot, dict):
            findings.append(f"{ci_id}: missing spec.aasu.snapshot")
            continue

        def inspect_component(name: str, component: Any) -> None:
            if not isinstance(component, dict):
                return
            version = component.get("version")
            if isinstance(version, str) and _is_unpinned_version(version):
                findings.append(f"{ci_id}: component {name} uses unpinned version '{version}'")

        for key in ("P", "M", "R", "K"):
            inspect_component(key, snapshot.get(key))
        tools = snapshot.get("T")
        if isinstance(tools, list):
            for idx, tool in enumerate(tools):
                inspect_component(f"T[{idx}]", tool)

        has_attestation = False
        for rel_type, src in incoming.get(ci_id, []):
            if rel_type != "attests":
                continue
            src_obj = assets_by_id.get(src)
            if isinstance(src_obj, dict) and _ci_type(src_obj) == "attestation_bundle":
                has_attestation = True
                break
        if not has_attestation:
            findings.append(f"{ci_id}: missing attestation_bundle -> attests relationship")

        model_component = snapshot.get("M")
        model_id = model_component.get("asset") if isinstance(model_component, dict) else None
        if isinstance(model_id, str):
            model_has_aibom = False
            for rel_type, src in incoming.get(model_id, []):
                if rel_type != "attests":
                    continue
                src_obj = assets_by_id.get(src)
                if isinstance(src_obj, dict) and _ci_type(src_obj) == "aibom_document":
                    model_has_aibom = True
                    break
            if not model_has_aibom:
                findings.append(f"{ci_id}: model '{model_id}' has no incoming attests edge from aibom_document")

        outgoing_rels = outgoing.get(ci_id, [])
        if not any(rel_type == "uses_short_term_memory" for rel_type, _ in outgoing_rels):
            findings.append(f"{ci_id}: missing uses_short_term_memory relationship")
        if not any(rel_type == "uses_long_term_memory" for rel_type, _ in outgoing_rels):
            findings.append(f"{ci_id}: missing uses_long_term_memory relationship")

    if findings:
        print("POLICY CHECK FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("OK: policy checks passed for production AASUs.")
    return 0


def cmd_memory_audit(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()
    if not args.skip_validate:
        base_rc = validate_registry_dir(registry_dir)
        if base_rc != 0:
            return base_rc

    assets_by_id, relationships = _load_assets_and_relationships(registry_dir)
    outgoing, _ = _index_relationships(relationships)
    findings: list[str] = []

    print("## Memory Audit")
    for ci_id, obj in sorted(assets_by_id.items()):
        if _ci_type(obj) != "aasu":
            continue
        rels = outgoing.get(ci_id, [])
        stm = [dst for rel_type, dst in rels if rel_type == "uses_short_term_memory"]
        ltm = [dst for rel_type, dst in rels if rel_type == "uses_long_term_memory"]
        print(f"- `{ci_id}`")
        print(f"  - short-term memory profiles: {', '.join(stm) if stm else 'none'}")
        print(f"  - long-term memory profiles: {', '.join(ltm) if ltm else 'none'}")

        if len(stm) != 1:
            findings.append(f"{ci_id}: expected exactly one short-term memory profile, found {len(stm)}")
        if _is_prod_aasu(obj) and len(ltm) != 1:
            findings.append(f"{ci_id}: production AASU expected exactly one long-term memory profile, found {len(ltm)}")

    for ci_id, obj in sorted(assets_by_id.items()):
        typ = _ci_type(obj)
        if typ not in {"memory_short_term_profile", "memory_long_term_profile"}:
            continue
        stores = [dst for rel_type, dst in outgoing.get(ci_id, []) if rel_type == "stores_memory_in"]
        print(f"- `{ci_id}` stores memory in: {', '.join(stores) if stores else 'none'}")
        if not stores:
            findings.append(f"{ci_id}: missing stores_memory_in relationship")

    if findings:
        print("")
        print("MEMORY AUDIT FINDINGS")
        for finding in findings:
            print(f"- {finding}")
        return 1 if args.strict else 0

    print("")
    print("OK: memory audit passed.")
    return 0


def cmd_attest_verify(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()
    if not args.skip_validate:
        base_rc = validate_registry_dir(registry_dir)
        if base_rc != 0:
            return base_rc

    assets_by_id, relationships = _load_assets_and_relationships(registry_dir)
    outgoing, incoming = _index_relationships(relationships)
    findings: list[str] = []

    for ci_id, obj in sorted(assets_by_id.items()):
        if _ci_type(obj) != "attestation_bundle":
            continue
        targets = [dst for rel_type, dst in outgoing.get(ci_id, []) if rel_type == "attests"]
        if not targets:
            findings.append(f"{ci_id}: attestation_bundle has no outgoing attests relationships")

    for ci_id, obj in sorted(assets_by_id.items()):
        if not _is_prod_aasu(obj):
            continue
        attest_sources = [
            src
            for rel_type, src in incoming.get(ci_id, [])
            if rel_type == "attests" and _ci_type(assets_by_id.get(src, {})) == "attestation_bundle"
        ]
        if not attest_sources:
            findings.append(f"{ci_id}: production AASU has no attestation_bundle attesting it")

    for ci_id, obj in sorted(assets_by_id.items()):
        if _ci_type(obj) != "aibom_document":
            continue
        targets = [dst for rel_type, dst in outgoing.get(ci_id, []) if rel_type == "attests"]
        if not targets:
            findings.append(f"{ci_id}: aibom_document has no outgoing attests relationships")

    if findings:
        print("ATTEST VERIFY FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("OK: attestation relationships are present.")
    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry).resolve()
    assets_by_id, aasu_reverse_refs = _load_registry_index(registry_dir)

    if args.changed_files_json:
        raw_entries = _read_changed_files_from_json(Path(args.changed_files_json))
    elif args.changed_files_file:
        raw_entries = _read_changed_files_from_lines(Path(args.changed_files_file))
    else:
        error("Provide --changed-files-json or --changed-files-file.")
        return 2

    changed_files = [_normalize_changed_file_entry(e) for e in raw_entries]

    assets_changed: list[dict[str, Any]] = []
    rels_changed: list[dict[str, Any]] = []
    other_files: list[dict[str, Any]] = []

    asset_types_counter: dict[str, int] = defaultdict(int)
    prod_assets: list[str] = []
    impacted_aasus: set[str] = set()

    for entry in changed_files:
        filename = entry["filename"]
        status = entry["status"]
        previous_filename = entry.get("previous_filename")
        path = (registry_dir.parent / filename).resolve()

        def add_other(kind: str) -> None:
            other_files.append(
                {"path": filename, "status": status, "kind": kind, "previous_path": previous_filename}
            )

        if not filename.startswith("registry/"):
            add_other("non-registry")
            continue

        if filename.startswith("registry/assets/"):
            if not path.exists():
                assets_changed.append(
                    {
                        "path": filename,
                        "status": status,
                        "previous_path": previous_filename,
                        "deleted": True,
                    }
                )
                continue

            try:
                obj = load_yaml_file(path)
            except Exception as exc:  # noqa: BLE001
                assets_changed.append({"path": filename, "status": status, "error": str(exc)})
                continue

            if not isinstance(obj, dict):
                assets_changed.append({"path": filename, "status": status, "error": "Not a YAML object"})
                continue

            ci_id = _read_nested(obj, ["metadata", "id"])
            ci_name = _read_nested(obj, ["metadata", "name"])
            ci_owners = _read_nested(obj, ["metadata", "owners"])
            spec_type = _read_nested(obj, ["spec", "type"])
            env = _read_nested(obj, ["spec", "environment"])

            record: dict[str, Any] = {
                "path": filename,
                "status": status,
                "previous_path": previous_filename,
                "ci_id": ci_id if isinstance(ci_id, str) else None,
                "name": ci_name if isinstance(ci_name, str) else None,
                "type": spec_type if isinstance(spec_type, str) else None,
                "environment": env if isinstance(env, str) else None,
                "owners": _format_owner_list(ci_owners),
            }

            if record["type"]:
                asset_types_counter[str(record["type"])] += 1

            if record["environment"] == "prod":
                if isinstance(record.get("ci_id"), str):
                    prod_assets.append(record["ci_id"])

            if isinstance(record.get("ci_id"), str):
                ci_id_str = record["ci_id"]
                if record.get("type") == "aasu":
                    impacted_aasus.add(ci_id_str)
                for aasu_id in aasu_reverse_refs.get(ci_id_str, set()):
                    impacted_aasus.add(aasu_id)

            if record.get("type") == "aasu":
                fingerprint = _read_nested(obj, ["spec", "aasu", "fingerprint", "value"])
                record["aasu_fingerprint"] = fingerprint if isinstance(fingerprint, str) else None

            assets_changed.append(record)
            continue

        if filename.startswith("registry/relationships/"):
            if not path.exists():
                rels_changed.append(
                    {
                        "path": filename,
                        "status": status,
                        "previous_path": previous_filename,
                        "deleted": True,
                    }
                )
                continue

            try:
                obj = load_yaml_file(path)
            except Exception as exc:  # noqa: BLE001
                rels_changed.append({"path": filename, "status": status, "error": str(exc)})
                continue

            if not isinstance(obj, dict):
                rels_changed.append({"path": filename, "status": status, "error": "Not a YAML object"})
                continue

            rel_id = _read_nested(obj, ["metadata", "id"])
            rel_type = _read_nested(obj, ["spec", "type"])
            rel_from = _read_nested(obj, ["spec", "from"])
            rel_to = _read_nested(obj, ["spec", "to"])
            rels_changed.append(
                {
                    "path": filename,
                    "status": status,
                    "previous_path": previous_filename,
                    "relationship_id": rel_id if isinstance(rel_id, str) else None,
                    "type": rel_type if isinstance(rel_type, str) else None,
                    "from": rel_from if isinstance(rel_from, str) else None,
                    "to": rel_to if isinstance(rel_to, str) else None,
                }
            )
            continue

        if filename.startswith("registry/schemas/"):
            add_other("schema")
            continue

        add_other("registry-other")

    summary = {
        "files_changed": len(changed_files),
        "assets_changed": len(assets_changed),
        "relationships_changed": len(rels_changed),
        "asset_types_changed": dict(sorted(asset_types_counter.items(), key=lambda kv: (-kv[1], kv[0]))),
        "prod_impacted": len(prod_assets) > 0,
        "prod_assets": sorted(set(prod_assets)),
        "impacted_aasus": sorted(impacted_aasus),
    }

    payload = {
        "summary": summary,
        "changes": {
            "assets": sorted(
                assets_changed,
                key=lambda r: (str(r.get("type") or ""), str(r.get("ci_id") or ""), str(r.get("path") or "")),
            ),
            "relationships": sorted(
                rels_changed,
                key=lambda r: (str(r.get("type") or ""), str(r.get("relationship_id") or ""), str(r.get("path") or "")),
            ),
            "other_files": sorted(other_files, key=lambda r: (str(r.get("kind") or ""), str(r.get("path") or ""))),
        },
    }

    if args.format == "json":
        out_text = _dump_json(payload, pretty=args.pretty)
    else:
        lines: list[str] = ["## AASU Registry Impact Report", ""]
        lines.append(f"- Files changed: **{summary['files_changed']}**")
        lines.append(f"- Assets changed: **{summary['assets_changed']}**")
        if summary["asset_types_changed"]:
            types_str = ", ".join(f"{k}:{v}" for k, v in summary["asset_types_changed"].items())
            lines.append(f"- Asset types: {types_str}")
        lines.append(f"- Relationships changed: **{summary['relationships_changed']}**")
        lines.append(f"- Production impact: **{'YES' if summary['prod_impacted'] else 'NO'}**")
        if summary["prod_assets"]:
            lines.append(f"  - Prod assets: {', '.join(summary['prod_assets'])}")
        if summary["impacted_aasus"]:
            lines.append(f"- Impacted AASUs: {', '.join(summary['impacted_aasus'])}")
        lines.append("")

        if payload["changes"]["assets"]:
            lines.append("### Assets")
            for a in payload["changes"]["assets"]:
                ci_id = a.get("ci_id") or a.get("path")
                typ = a.get("type") or "unknown"
                status = a.get("status") or "changed"
                env = a.get("environment")
                suffix = f" env={env}" if env else ""
                lines.append(f"- `{ci_id}` ({typ}) [{status}]{suffix}")
                if a.get("aasu_fingerprint"):
                    lines.append(f"  - fingerprint: `{a['aasu_fingerprint']}`")
                if a.get("owners"):
                    lines.append(f"  - owners: {', '.join(a['owners'])}")
            lines.append("")

        if payload["changes"]["relationships"]:
            lines.append("### Relationships")
            for r in payload["changes"]["relationships"]:
                rid = r.get("relationship_id") or r.get("path")
                rtype = r.get("type") or "rel"
                status = r.get("status") or "changed"
                lines.append(f"- `{rid}` ({rtype}) [{status}]")
                frm = r.get("from")
                to = r.get("to")
                if frm and to:
                    lines.append(f"  - `{frm}` -> `{to}`")
            lines.append("")

        lines.append("### Next steps")
        lines.append("- Run `python3 tools/aasu_registry.py validate`.")
        lines.append("- Run `python3 tools/aasu_registry.py policy-check` for regulated policy gates.")
        lines.append("- If you changed any AASU snapshot `(P,M,R,T,K)`, run `python3 tools/aasu_registry.py fingerprint --all --write`.")
        out_text = "\n".join(lines).rstrip() + "\n"

    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")
        print(f"WROTE: {args.out}")
        return 0

    sys.stdout.write(out_text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aasu-registry", description="Operate the AASU CMDB-as-code registry.")
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY_DIR),
        help="Path to registry directory (default: ./registry)",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_validate = sub.add_parser("validate", help="Validate registry manifests (schemas, graph integrity, fingerprints).")
    p_validate.set_defaults(func=cmd_validate)

    p_fp = sub.add_parser("fingerprint", help="Check or update AASU snapshot fingerprints.")
    target = p_fp.add_mutually_exclusive_group(required=True)
    target.add_argument("--file", help="Path to a single AASU CI manifest YAML.")
    target.add_argument("--all", action="store_true", help="Process all AASU CI manifests in the registry.")
    p_fp.add_argument("--write", action="store_true", help="Write updated fingerprints in-place.")
    p_fp.set_defaults(func=cmd_fingerprint)

    p_export = sub.add_parser("export", help="Export registry manifests as JSON (for downstream tooling/CMDB sync).")
    p_export.add_argument("--out", help="Write JSON to a file instead of stdout.")
    p_export.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    p_export.set_defaults(func=cmd_export)

    p_graph = sub.add_parser("graph", help="Render relationship graph (Mermaid).")
    p_graph.add_argument("--format", default="mermaid", choices=["mermaid"])
    p_graph.add_argument("--out", help="Write graph output to a file instead of stdout.")
    p_graph.set_defaults(func=cmd_graph)

    p_impact = sub.add_parser("impact", help="Summarize impact of a PR/change-set for review/audit workflows.")
    p_impact.add_argument("--changed-files-json", help="Path to GitHub listFiles-style JSON.")
    p_impact.add_argument("--changed-files-file", help="Path to newline-separated list of changed files.")
    p_impact.add_argument("--format", default="markdown", choices=["markdown", "json"])
    p_impact.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p_impact.add_argument("--out", help="Write output to a file instead of stdout.")
    p_impact.set_defaults(func=cmd_impact)

    p_policy = sub.add_parser(
        "policy-check",
        help="Run policy checks for regulated-ready AASU governance (pinning, memory links, attestations).",
    )
    p_policy.add_argument("--skip-validate", action="store_true", help="Skip base schema/graph/fingerprint validation.")
    p_policy.set_defaults(func=cmd_policy_check)

    p_memory = sub.add_parser(
        "memory-audit",
        help="Summarize AASU short/long-term memory relationships and storage bindings.",
    )
    p_memory.add_argument("--skip-validate", action="store_true", help="Skip base schema/graph/fingerprint validation.")
    p_memory.add_argument("--strict", action="store_true", help="Return non-zero if audit findings exist.")
    p_memory.set_defaults(func=cmd_memory_audit)

    p_attest = sub.add_parser(
        "attest-verify",
        help="Verify attestation bundle and AIBOM attestation relationships are present.",
    )
    p_attest.add_argument("--skip-validate", action="store_true", help="Skip base schema/graph/fingerprint validation.")
    p_attest.set_defaults(func=cmd_attest_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
