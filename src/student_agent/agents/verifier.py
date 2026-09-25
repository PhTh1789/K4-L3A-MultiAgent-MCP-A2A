from typing import Any
from ..mcp_gateway import EvidenceGateway
from ..trace import TraceWriter

class VerifierAgent:
    """Verifier Agent phụ trách bởi Thịnh."""
    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter):
        self.gateway = gateway
        self.trace = trace

    def run(self, case_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Kiểm tra chéo và xuất kết quả cuối cùng theo Schema (Thịnh)"""
        # TODO: Xác minh consistency, gộp dữ liệu từ các agents, tính confidence
        self.trace.emit(
            case_id=case_id,
            event_type="verification_completed",
            actor="verifier"
        )
        
        # Schema mẫu ban đầu (Cần thay thế bằng kết quả thật sau khi logic hoàn thiện)
        return {
            "schema_version": "day09-l3a-output-v2",
            "case_id": case_id,
            "assessment": {
                "primary_issue": "insufficient_evidence",
                "case_status": "needs_investigation",
                "confidence": 0.0
            },
            "affected_entities": {
                "order_ids": [],
                "item_ids": [],
                "seller_ids": [],
                "payment_references": [],
                "shipment_ids": []
            },
            "claim_assessments": [],
            "root_cause_analysis": {
                "ranked_causes": [],
                "responsible_parties": []
            },
            "evidence_refs": [],
            "data_conflicts": [],
            "financial_resolution": {
                "currency": "BRL",
                "recommended_refund_brl": 0,
                "refund_lines": []
            },
            "resolution_actions": []
        }
