"""Strict, optional Track-D metric-registry verification for the developer copy."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


SUPPORTED_SCHEMA = "fsr-track-d-metric-registry-v1"
NUMERIC_STATUSES = {"REAGGREGATED", "SOURCE_ONLY", "UNAVAILABLE", "NOT_CHECKED"}
DEFINITION_STATUSES = {"DEFINED", "SOURCE_ONLY", "MISSING", "NOT_APPLICABLE"}


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def values_match(left, right) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(values_match(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(values_match(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)
    return left == right


def inventory_ids(value, label: str, errors: list[str]) -> tuple[list[str], list[str]]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return [], []
    invalid = [item for item in value if not isinstance(item, str) or not item]
    if invalid:
        errors.append(f"{label} contains missing or non-string metric ids")
    ids = [item for item in value if isinstance(item, str) and item]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"{label} contains duplicate metric id: {', '.join(duplicates)}")
    return ids, duplicates


def _metric_marker(metric: dict, errors: list[str], source_unchecked: list[str]) -> tuple[str, dict]:
    metric_id = metric.get("id")
    status = metric.get("numeric_status")
    definition = metric.get("definition_status")
    reasons = []
    if status not in NUMERIC_STATUSES:
        reasons.append("numeric_status missing or invalid")
    if definition not in DEFINITION_STATUSES:
        reasons.append("definition_status missing or invalid")

    source = metric.get("source", {})
    if not isinstance(source, dict):
        source = {}
    source_path = Path(source.get("path", ""))
    if not source_path.is_file():
        reasons.append("source file missing")
    elif digest_path(source_path) != source.get("sha256"):
        reasons.append("source hash stale or mismatched")
    if not source.get("locator"):
        reasons.append("source locator absent")

    definition_source = metric.get("definition_source")
    if definition_source is not None:
        if not isinstance(definition_source, dict):
            reasons.append("definition source is not an object")
            definition_source = {}
        definition_path = Path(definition_source.get("path", ""))
        if not definition_path.is_file():
            reasons.append("definition source file missing")
        elif digest_path(definition_path) != definition_source.get("sha256"):
            reasons.append("definition source hash stale or mismatched")
        if not definition_source.get("locator"):
            reasons.append("definition source locator absent")

    if status == "REAGGREGATED":
        check = metric.get("independent_check", {})
        if not isinstance(check, dict) or check.get("status") != "PASS":
            reasons.append("REAGGREGATED metric lacks a passing independent check")
        if definition != "DEFINED":
            reasons.append("REAGGREGATED metric lacks a source-grounded definition")
        if not isinstance(check, dict) or "reported_value" not in check or "recomputed_value" not in check:
            reasons.append("independent check lacks reported/recomputed values")
        elif not values_match(check["reported_value"], check["recomputed_value"]):
            reasons.append("reported and recomputed values differ")
    else:
        source_unchecked.append(metric_id)
        if not metric.get("scope") or not metric.get("limitation"):
            reasons.append("source-only/unavailable metric lacks explicit scope and limitation")
        if status == "UNAVAILABLE" and definition == "DEFINED" and metric.get("source_claim") is None:
            reasons.append("unavailable metric lacks a source claim explaining absence")

    if definition == "MISSING" and status == "REAGGREGATED":
        reasons.append("missing class/metric definition cannot be mechanically accepted")
    if reasons:
        errors.extend(f"{metric_id}: {reason}" for reason in reasons)
    marker = {
        "numeric_status": status,
        "definition_status": definition,
        "provenance_status": "PASS" if not reasons else "FAIL",
        "acceptance_marker": (
            "RECOMPUTED_WITH_SOURCE_DEFINITION" if status == "REAGGREGATED" and not reasons
            else "SOURCE_ONLY_DECLARED" if status == "SOURCE_ONLY" and not reasons
            else "UNAVAILABLE_DECLARED" if status == "UNAVAILABLE" and not reasons
            else "NOT_CHECKED_DECLARED" if status == "NOT_CHECKED" and not reasons
            else "UNVERIFIED"
        ),
        "reasons": reasons,
    }
    return metric_id, marker


def evaluate_registry(registry: dict, registry_path: Path, output_record_path: Path | None = None) -> dict:
    """Return a hash-bound verdict for the supported registry contract."""
    errors: list[str] = []
    warnings: list[str] = []
    registry_sha256 = digest_path(registry_path) if registry_path.is_file() else None
    if not isinstance(registry, dict):
        errors.append("registry root must be an object")
        return {
            "status": "CANDIDATE",
            "schema": None,
            "registry_sha256": registry_sha256,
            "errors": errors,
            "warnings": warnings,
        }
    schema = registry.get("schema")
    if schema != SUPPORTED_SCHEMA:
        errors.append(f"unsupported metric registry schema: {schema!r}")

    projection = registry.get("record_projection")
    declared_ids, declared_duplicates = inventory_ids(
        registry.get("declared_metric_ids", []), "declared_metric_ids", errors
    )
    projection_ids, projection_duplicates = inventory_ids(
        projection.get("metric_ids", []) if isinstance(projection, dict) else [],
        "record_projection.metric_ids",
        errors,
    )
    expected_projection_hash = registry.get("record_sha256")
    actual_projection_hash = digest_bytes(canonical(projection)) if projection is not None else None
    if expected_projection_hash != actual_projection_hash:
        errors.append("record projection hash is stale or missing")

    attestation = registry.get("mechanical_attestation", {})
    mechanical_ok = (
        isinstance(attestation, dict)
        and attestation.get("status") == "PASS"
        and attestation.get("record_sha256") == actual_projection_hash
    )
    if not mechanical_ok:
        warnings.append("mechanical attestation is absent, failed, or stale")

    metrics = registry.get("metrics", [])
    if not isinstance(metrics, list):
        errors.append("metrics must be a list")
        metrics = []
    registry_inventory_ids = [metric.get("id") for metric in metrics if isinstance(metric, dict)]
    registry_ids, registry_duplicates = inventory_ids(registry_inventory_ids, "metrics[].id", errors)

    markers = {}
    seen = set()
    source_unchecked = []
    for metric in metrics:
        if not isinstance(metric, dict):
            errors.append("metrics contains a non-object entry")
            continue
        metric_id = metric.get("id")
        if not metric_id or metric_id in seen:
            errors.append(f"missing or duplicate metric id: {metric_id!r}")
            continue
        seen.add(metric_id)
        checked_id, markers[metric_id] = _metric_marker(metric, errors, source_unchecked)
        if checked_id != metric_id:
            errors.append(f"metric id changed while checking: {metric_id!r}")

    projection_set = set(projection_ids)
    declared_set = set(declared_ids)
    registry_set = set(registry_ids)
    inventory_equal = projection_set == declared_set == registry_set
    if not inventory_equal:
        errors.append(
            "metric inventory mismatch: "
            f"projection_only={sorted(projection_set - declared_set)}; "
            f"declared_only={sorted(declared_set - projection_set)}; "
            f"registry_only={sorted(registry_set - declared_set)}; "
            f"declared_missing_registry={sorted(declared_set - registry_set)}"
        )
    missing = sorted(declared_set - seen)
    if missing:
        errors.append("declared metrics missing registry entries: " + ", ".join(missing))
    undeclared = sorted(seen - declared_set)
    if undeclared:
        errors.append("registry contains metrics not declared by record: " + ", ".join(undeclared))

    all_explicit = bool(metrics) and all(
        marker["numeric_status"] in NUMERIC_STATUSES for marker in markers.values()
    )
    status = "PASS" if not errors and mechanical_ok and inventory_equal and all_explicit else "CANDIDATE"
    numeric_scope = "REAGGREGATED" if not source_unchecked and status == "PASS" else "PARTIAL_EXPLICIT_SCOPE"
    result = {
        "status": status,
        "schema": schema,
        "registry_sha256": registry_sha256,
        "record_projection_sha256": actual_projection_hash,
        "output_record_sha256": digest_path(output_record_path) if output_record_path and output_record_path.is_file() else None,
        "mechanical_status": "MECHANICAL_PASS" if mechanical_ok else "MECHANICAL_NOT_VERIFIED",
        "report_integrity_status": status,
        "numeric_scope_status": numeric_scope,
        "metric_markers": markers,
        "source_unchecked_metrics": sorted(source_unchecked),
        "metric_inventory": {
            "status": "PASS" if inventory_equal and not (
                projection_duplicates or declared_duplicates or registry_duplicates
            ) else "FAIL",
            "exact_set_equality": inventory_equal,
            "record_projection_metric_ids": sorted(projection_set),
            "declared_metric_ids": sorted(declared_set),
            "registry_metric_ids": sorted(registry_set),
            "duplicates": {
                "record_projection.metric_ids": projection_duplicates,
                "declared_metric_ids": declared_duplicates,
                "metrics[].id": registry_duplicates,
            },
        },
        "original_research": {
            "status": registry.get("original_research", {}).get("status", "NOT_SPECIFIED")
            if isinstance(registry.get("original_research", {}), dict) else "NOT_SPECIFIED",
            "blocking": False,
            "reason": "original algorithm/training/simulation rerun is outside FSR scope",
        },
        "marker_propagation": {
            "mechanical_pass_does_not_override_metric_markers": True,
            "source_unchecked_count": len(source_unchecked),
            "all_metric_ids_propagated": inventory_equal and sorted(markers) == sorted(declared_ids),
        },
        "deployment_readiness": "CONDITIONAL_DEVELOPER_COPY_ONLY" if status == "PASS" else "NOT_READY",
        "warnings": warnings,
        "errors": errors,
    }
    return result
