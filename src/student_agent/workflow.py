from __future__ import annotations

from typing import Any

from .mcp_gateway import EvidenceGateway
from .trace import TraceWriter
from .agents.coordinator import CoordinatorAgent
from .agents.order_shipment import OrderShipmentAgent
from .agents.payment_policy import PaymentPolicyAgent
from .agents.verifier import VerifierAgent


async def solve_case(
    case: dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> dict[str, Any]:
    """L3A multi-agent workflow entry point."""
    case_id = case["case_id"]
    
    # 1. Khởi tạo các Agents
    coordinator = CoordinatorAgent(gateway, trace)
    order_shipment = OrderShipmentAgent(gateway, trace)
    payment_policy = PaymentPolicyAgent(gateway, trace)
    verifier = VerifierAgent(gateway, trace)
    
    # 2. Coordinator phân tích sơ bộ và chuẩn bị context
    context = await coordinator.run(case)
    
    # 3. Chuyển giao công việc (Handoff) cho các Specialist Agents
    trace.emit(case_id=case_id, event_type="handoff", actor="coordinator", target="order_shipment_agent")
    context["fulfillment"] = await order_shipment.run(case_id, context)
    
    trace.emit(case_id=case_id, event_type="handoff", actor="coordinator", target="payment_policy_agent")
    context["finance"] = await payment_policy.run(case_id, context)
    
    # 4. Chuyển kết quả về Verifier để thẩm định và xuất output
    trace.emit(case_id=case_id, event_type="handoff", actor="coordinator", target="verifier")
    final_output = verifier.run(case_id, context)
    
    return final_output
