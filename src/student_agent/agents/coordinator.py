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
        """Tiếp nhận case, phân tích sơ bộ và chuẩn bị context chia task."""
        case_id = case["case_id"]
        
        # Emit event báo hiệu đã nhận case và chia task
        self.trace.emit(
            case_id=case_id,
            event_type="task_assigned",
            actor="coordinator",
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
