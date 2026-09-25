from __future__ import annotations

from typing import Any

from ..mcp_gateway import EvidenceGateway
from ..trace import TraceWriter


class CoordinatorAgent:
    """Prepare a bounded, auditable task context for specialist agents."""

    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter):
        self.gateway = gateway
        self.trace = trace

    async def run(self, case: dict[str, Any]) -> dict[str, Any]:
<<<<<<< HEAD
        """Accept a case and preserve only input needed downstream."""
=======
        """Tiếp nhận case, phân tích sơ bộ và chuẩn bị context chia task."""
        case_id = case["case_id"]
        
        # Emit event báo hiệu đã nhận case và chia task
>>>>>>> 0fd2fda423711fdf0f24264a8859d30a024c2485
        self.trace.emit(
            case_id=case_id,
            event_type="task_assigned",
            actor="coordinator",
<<<<<<< HEAD
            target="order_shipment_agent",
            attributes={"specialists": 2},
        )
        customer_request = case.get("customer_request")
        if not isinstance(customer_request, dict):
            customer_request = {}

        claimed_order_id = customer_request.get("claimed_order_id")
        if not isinstance(claimed_order_id, str) or not claimed_order_id.strip():
            claimed_order_id = case.get("claimed_order_id")
        if not isinstance(claimed_order_id, str):
            claimed_order_id = None

        claims = case.get("claims")
        if not isinstance(claims, list):
            claims = customer_request.get("claims")
        if not isinstance(claims, list):
            claims = []

        policy_version = case.get("policy_version")
        if not isinstance(policy_version, str):
            policy_version = customer_request.get("policy_version")
        if not isinstance(policy_version, str):
            policy_version = ""

        return {
            "case_info": case,
            "claimed_order_id": claimed_order_id,
            "claims": claims,
            "policy_version": policy_version,
        }
=======
            target="specialists",
            attributes={
                "customer_claims_count": len(case.get("claims", []))
            }
        )
        
        # Khởi tạo Context để các Agent phía sau điền dữ liệu vào
        # Đây chính là "giao kèo" dữ liệu (Data Contract)
        context = {
            "case_info": case,
            "fulfillment": {},  # Nhánh của Dương sẽ điền vào đây
            "finance": {}       # Nhánh của Lương sẽ điền vào đây
        }
        
        return context

>>>>>>> 0fd2fda423711fdf0f24264a8859d30a024c2485
