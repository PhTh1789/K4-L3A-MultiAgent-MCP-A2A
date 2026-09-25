from typing import Any
from ..mcp_gateway import EvidenceGateway
from ..trace import TraceWriter

class OrderShipmentAgent:
    """Order, Item & Shipment Agent phụ trách bởi Dương."""
    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter):
        self.gateway = gateway
        self.trace = trace

    async def run(self, case_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Phụ trách mảng Đơn hàng, Sản phẩm & Vận chuyển (Dương)"""
        # TODO: Cài đặt logic gọi get_order, get_order_items, get_seller, get_shipment...
        # self.trace.emit(case_id=case_id, event_type="tool_result_consumed", ...)
        return {"order_data": {}, "shipment_data": {}, "affected_entities": {}}
