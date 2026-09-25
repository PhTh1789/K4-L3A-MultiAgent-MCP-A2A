from __future__ import annotations

from typing import Any

from ..mcp_gateway import EvidenceGateway, call_with_retry
from ..trace import TraceWriter


class PaymentPolicyAgent:
    """Collect payment/refund evidence and evaluate the applicable policy."""

    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter):
        self.gateway = gateway
        self.trace = trace

    async def run(self, case_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Fetch payment lifecycle evidence and the policy named by the case."""
        order_id = context.get("claimed_order_id")
        if not isinstance(order_id, str) or not order_id:
            return {"evidence": {}, "data": {}, "errors": ["missing claimed order id"]}

        requests: list[tuple[str, dict[str, str]]] = [
            ("get_order_payments", {"order_id": order_id}),
            ("get_payment_timeline", {"order_id": order_id}),
            ("get_refund_timeline", {"order_id": order_id}),
        ]
        policy_version = context.get("policy_version")
        if isinstance(policy_version, str) and policy_version:
            requests.append(("get_policy", {"policy_version": policy_version}))

        evidence: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        for tool_name, arguments in requests:
            try:
                result = await call_with_retry(
                    self.gateway,
                    tool_name,
                    case_id=case_id,
                    **arguments,
                )
            except Exception as error:
                errors.append(f"{tool_name}: {type(error).__name__}")
                continue
            evidence[tool_name] = result
            self.trace.emit(
                case_id=case_id,
                event_type="tool_result_consumed",
                actor="payment_policy_agent",
                tool_name=tool_name,
                evidence_refs=[result["evidence_ref"]],
                attributes={"domain": result["domain"]},
            )

        self.trace.emit(
            case_id=case_id,
            event_type="policy_decided",
            actor="payment_policy_agent",
            decision_code="policy_evidence_collected",
            evidence_refs=[
                evidence["get_policy"]["evidence_ref"]
            ]
            if "get_policy" in evidence
            else None,
            attributes={"policy_available": "get_policy" in evidence},
        )
        return {
            "evidence": evidence,
            "data": {name: value["data"] for name, value in evidence.items()},
            "errors": errors,
        }
