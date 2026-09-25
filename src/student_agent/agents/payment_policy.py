from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..mcp_gateway import EvidenceGateway
from ..trace import TraceWriter

_ORDER_ID_KEYS = frozenset({"order_id", "order_ids"})
_PAYMENT_REFERENCE_KEYS = frozenset(
    {
        "payment_id",
        "payment_ids",
        "payment_reference",
        "payment_references",
        "transaction_id",
        "transaction_ids",
        "transaction_reference",
        "transaction_references",
    }
)
_STATUS_KEYS = frozenset({"event", "event_type", "payment_status", "state", "status"})
_PAYMENT_METHOD_KEYS = frozenset(
    {"method", "payment_method", "payment_methods", "payment_type", "payment_types"}
)
_DUPLICATE_KEYS = frozenset(
    {"duplicate", "duplicate_charge", "duplicate_of", "is_duplicate"}
)
_POLICY_VERSION_KEYS = frozenset({"policy_version", "policy_versions"})
_CLAIMS_KEYS = frozenset({"claims"})
_CLAIM_KIND_KEYS = ("claim_type", "issue", "reason_code", "type")
_PAYMENT_CLAIM_KINDS = frozenset(
    {
        "duplicate_charge",
        "payment_mismatch",
        "refund_failed",
        "refund_pending",
        "valid_split_payment",
    }
)


def _iter_keyed_values(value: Any, wanted_keys: frozenset[str]) -> Iterable[Any]:
    """Yield values whose field name is authoritative enough for extraction."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in wanted_keys:
                yield child
            yield from _iter_keyed_values(child, wanted_keys)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_keyed_values(child, wanted_keys)


def _flatten_strings(values: Iterable[Any]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                flattened.append(candidate.strip())
    return list(dict.fromkeys(flattened))


def _extract_strings(value: Any, keys: frozenset[str]) -> list[str]:
    return _flatten_strings(_iter_keyed_values(value, keys))


def _contains_explicit_duplicate(value: Any) -> bool:
    for candidate in _iter_keyed_values(value, _DUPLICATE_KEYS):
        if candidate is True:
            return True
        if isinstance(candidate, str) and candidate.strip().lower() not in {
            "",
            "false",
            "no",
            "none",
            "null",
        }:
            return True

    status_tokens = (status.lower() for status in _extract_strings(value, _STATUS_KEYS))
    return any("duplicate" in status for status in status_tokens)


def _record_count(data: Any, collection_keys: tuple[str, ...]) -> int:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, Mapping):
        for key in collection_keys:
            records = data.get(key)
            if isinstance(records, list):
                return len(records)
        return int(bool(data))
    return 0


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", " ").split())


def _extract_claims(context: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for value in _iter_keyed_values(context, _CLAIMS_KEYS):
        if not isinstance(value, list):
            continue
        for claim in value:
            if not isinstance(claim, Mapping):
                continue
            claim_id = claim.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id or claim_id in seen_ids:
                continue
            claims.append(dict(claim))
            seen_ids.add(claim_id)
    return claims


def _claim_kind(claim: Mapping[str, Any]) -> str | None:
    for key in _CLAIM_KIND_KEYS:
        value = claim.get(key)
        if isinstance(value, str) and value.strip():
            return _normalize_token(value)
    return None


def _payment_claim_assessments(
    claims: list[dict[str, Any]],
    issue_signals: dict[str, bool],
    payment_evidence_refs: list[str],
    refund_evidence_refs: list[str],
) -> list[dict[str, Any]]:
    assessments: list[dict[str, Any]] = []
    for claim in claims:
        kind = _claim_kind(claim)
        if kind not in _PAYMENT_CLAIM_KINDS:
            continue

        supported = issue_signals.get(kind, False)
        relevant_refs = (
            refund_evidence_refs
            if kind in {"refund_failed", "refund_pending"}
            else payment_evidence_refs
        )
        assessments.append(
            {
                "claim_id": claim["claim_id"],
                "verdict": "supported" if supported else "insufficient_evidence",
                "confidence": 0.9 if supported else 0.7,
                "evidence_refs": relevant_refs,
            }
        )
    return assessments


class PaymentPolicyAgent:
    """Collect authoritative payment and refund evidence for the policy stage."""

    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter) -> None:
        self.gateway = gateway
        self.trace = trace

    async def run(self, case_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Investigate payments for every structured order ID in this case.

        Policy decisions intentionally remain a later stage. This method never parses
        free-form customer text as ground truth and never manufactures evidence refs.
        """
        order_ids = _extract_strings(context, _ORDER_ID_KEYS)
        evidence_refs: list[str] = []
        payment_evidence_refs: list[str] = []
        refund_evidence_refs: list[str] = []
        payment_references: list[str] = []
        orders: dict[str, dict[str, Any]] = {}

        for order_id in order_ids:
            order_evidence: dict[str, Any] = {}
            for tool_name, result_key, expected_domain in (
                ("get_order_payments", "order_payments", "payment"),
                ("get_payment_timeline", "payment_timeline", "payment"),
                ("get_refund_timeline", "refund_timeline", "refund"),
            ):
                evidence = await self.gateway.call(
                    tool_name,
                    case_id=case_id,
                    order_id=order_id,
                )
                if evidence["domain"] != expected_domain:
                    raise ValueError(
                        f"{tool_name} returned domain {evidence['domain']!r}; "
                        f"expected {expected_domain!r}"
                    )

                evidence_ref = evidence["evidence_ref"]
                evidence_refs.append(evidence_ref)
                if expected_domain == "refund":
                    refund_evidence_refs.append(evidence_ref)
                else:
                    payment_evidence_refs.append(evidence_ref)
                payment_references.extend(
                    _extract_strings(evidence["data"], _PAYMENT_REFERENCE_KEYS)
                )
                order_evidence[result_key] = {
                    "evidence_ref": evidence_ref,
                    "data": evidence["data"],
                    "warnings": evidence.get("warnings", []),
                }
                self.trace.emit(
                    case_id=case_id,
                    event_type="tool_result_consumed",
                    actor="payment_agent",
                    tool_name=tool_name,
                    evidence_refs=[evidence_ref],
                    attributes={"order_id": order_id},
                )

            orders[order_id] = order_evidence

        evidence_refs = list(dict.fromkeys(evidence_refs))
        payment_references = list(dict.fromkeys(payment_references))
        payment_payloads = [order["order_payments"]["data"] for order in orders.values()]
        payment_timelines = [order["payment_timeline"]["data"] for order in orders.values()]
        refund_timelines = [order["refund_timeline"]["data"] for order in orders.values()]
        payment_statuses = _extract_strings(payment_timelines, _STATUS_KEYS)
        refund_statuses = _extract_strings(refund_timelines, _STATUS_KEYS)
        normalized_refund_statuses = {status.lower() for status in refund_statuses}
        issue_signals = {
            "duplicate_charge": _contains_explicit_duplicate(
                [*payment_payloads, *payment_timelines]
            ),
            "refund_pending": bool(
                normalized_refund_statuses
                & {"initiated", "pending", "processing", "requested"}
            ),
            "refund_failed": bool(
                normalized_refund_statuses
                & {"declined", "failed", "rejected", "reversed"}
            ),
        }

        policy_versions = _extract_strings(context, _POLICY_VERSION_KEYS)
        if len(policy_versions) > 1:
            raise ValueError(f"case contains multiple policy versions: {policy_versions}")

        policy_data: dict[str, Any] | None = None
        policy_evidence_ref: str | None = None
        policy_status = "missing_policy_version"
        if policy_versions:
            policy_version = policy_versions[0]
            policy_evidence = await self.gateway.call(
                "get_policy",
                case_id=case_id,
                policy_version=policy_version,
            )
            if policy_evidence["domain"] != "policy":
                raise ValueError(
                    "get_policy returned domain "
                    f"{policy_evidence['domain']!r}; expected 'policy'"
                )
            policy_evidence_ref = policy_evidence["evidence_ref"]
            policy_data = policy_evidence["data"]
            evidence_refs.append(policy_evidence_ref)
            self.trace.emit(
                case_id=case_id,
                event_type="tool_result_consumed",
                actor="policy_agent",
                tool_name="get_policy",
                evidence_refs=[policy_evidence_ref],
                attributes={"policy_version": policy_version},
            )
            policy_status = "evidence_collected"

        evidence_refs = list(dict.fromkeys(evidence_refs))
        payment_evidence_refs = list(dict.fromkeys(payment_evidence_refs))
        refund_evidence_refs = list(dict.fromkeys(refund_evidence_refs))
        claim_assessments = _payment_claim_assessments(
            _extract_claims(context),
            issue_signals,
            payment_evidence_refs,
            refund_evidence_refs,
        )

        return {
            "payment_data": {
                "orders": orders,
                "summary": {
                    "order_count": len(orders),
                    "payment_record_count": sum(
                        _record_count(payload, ("payments", "payment_rows", "records"))
                        for payload in payment_payloads
                    ),
                    "payment_statuses": payment_statuses,
                    "refund_statuses": refund_statuses,
                    "payment_methods": _extract_strings(payment_payloads, _PAYMENT_METHOD_KEYS),
                },
            },
            "payment_references": payment_references,
            "evidence_refs": evidence_refs,
            "issue_signals": issue_signals,
            "claim_assessments": claim_assessments,
            "policy": {
                "status": policy_status,
                "evidence_ref": policy_evidence_ref,
                "data": policy_data,
            },
            "financial_resolution_candidate": None,
            "resolution_actions": [],
            "status": "completed" if order_ids else "missing_order_id",
        }
