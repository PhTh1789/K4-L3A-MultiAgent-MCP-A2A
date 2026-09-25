from typing import Any
from ..mcp_gateway import EvidenceGateway
from ..trace import TraceWriter

class CoordinatorAgent:
    """Coordinator Agent phụ trách bởi Thịnh."""
    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter):
        self.gateway = gateway
        self.trace = trace

    async def run(self, case: dict[str, Any]) -> dict[str, Any]:
        """Tiếp nhận case, phân tích sơ bộ và chuẩn bị context chia task."""
        self.trace.emit(
            case_id=case["case_id"],
            event_type="task_assigned",
            actor="coordinator",
            target="specialists"
        )
        return {"case_info": case}
