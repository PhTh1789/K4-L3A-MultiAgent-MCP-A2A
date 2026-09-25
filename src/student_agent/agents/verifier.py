from __future__ import annotations

from typing import Any

from ..mcp_gateway import EvidenceGateway
from ..trace import TraceWriter
from .analysis import build_output


class VerifierAgent:
    """Cross-check specialist evidence and emit the contract-shaped result."""

    def __init__(self, gateway: EvidenceGateway, trace: TraceWriter):
        self.gateway = gateway
        self.trace = trace

    def run(self, case_id: str, context: dict[str, Any]) -> dict[str, Any]:
<<<<<<< HEAD
        output = build_output(context)
=======
        """Kiểm tra chéo và xuất kết quả cuối cùng theo Schema (Thịnh)"""
        
        # Lấy dữ liệu từ 2 nhánh (có default là dict rỗng nếu 2 bạn kia chưa code xong)
        fulfillment = context.get("fulfillment", {})
        finance = context.get("finance", {})
        
        # 1. Tổng hợp Evidence Refs từ cả 2 nhánh (loại bỏ trùng lặp)
        evidence_refs = list(set(
            fulfillment.get("evidence_refs", []) + finance.get("evidence_refs", [])
        ))
        
        # 2. Tổng hợp Affected Entities
        f_entities = fulfillment.get("affected_entities", {})
        fin_entities = finance.get("affected_entities", {})
        
        affected_entities = {
            "order_ids": list(set(f_entities.get("order_ids", []) + fin_entities.get("order_ids", []))),
            "item_ids": list(set(f_entities.get("item_ids", []) + fin_entities.get("item_ids", []))),
            "seller_ids": list(set(f_entities.get("seller_ids", []) + fin_entities.get("seller_ids", []))),
            "shipment_ids": list(set(f_entities.get("shipment_ids", []) + fin_entities.get("shipment_ids", []))),
            "payment_references": list(set(fin_entities.get("payment_references", [])))
        }
        
        # Lấy dữ liệu cơ sở từ nhánh Finance (Lương)
        # Sử dụng 'or' để đề phòng trường hợp các bạn kia return dict rỗng {}
        assessment = finance.get("assessment") or {
            "primary_issue": "insufficient_evidence",
            "case_status": "needs_investigation",
            "confidence": 0.0
        }
        root_cause_analysis = finance.get("root_cause_analysis") or {
            "ranked_causes": [],
            "responsible_parties": []
        }
        financial_resolution = finance.get("financial_resolution") or {
            "currency": "BRL",
            "recommended_refund_brl": 0.0,
            "refund_lines": []
        }
        # Schema bắt buộc phải có currency là BRL
        financial_resolution["currency"] = "BRL"
        
        resolution_actions = finance.get("resolution_actions") or []
        data_conflicts = (fulfillment.get("data_conflicts") or []) + (finance.get("data_conflicts") or [])

        
        primary_issue = assessment.get("primary_issue", "insufficient_evidence")

        # 3. KIỂM TRA CHÉO & ĐIỀU CHỈNH (Cross-field Consistency)
        # 3.1. Đảm bảo tổng refund_lines khớp recommended_refund_brl
        total_refund_lines = round(sum(line.get("amount_brl", 0) for line in financial_resolution.get("refund_lines", [])), 2)
        if abs(total_refund_lines - financial_resolution.get("recommended_refund_brl", 0)) > 0.01:
            financial_resolution["recommended_refund_brl"] = total_refund_lines
            
        # 3.2. Ràng buộc Action vs Status
        if assessment.get("case_status") == "action_required" and not resolution_actions:
            # Bắt buộc phải có action nếu status là action_required
            assessment["case_status"] = "needs_investigation"
            
        if assessment.get("case_status") == "no_action":
            # Không làm gì thì không được hoàn tiền hay ghi nhận actions
            financial_resolution["recommended_refund_brl"] = 0.0
            financial_resolution["refund_lines"] = []
            resolution_actions = []

        # 3.3. Ràng buộc trách nhiệm (Responsible Party)
        responsible_types = [p.get("party_type") for p in root_cause_analysis.get("responsible_parties", [])]
        if "late_delivery_seller" in primary_issue and "seller" not in responsible_types:
            root_cause_analysis["responsible_parties"].append({"party_type": "seller", "party_id": None})
        elif "late_delivery_logistics" in primary_issue and "logistics_provider" not in responsible_types:
            root_cause_analysis["responsible_parties"].append({"party_type": "logistics_provider", "party_id": None})

        # 4. TÍNH TOÁN ĐỘ TIN CẬY (Confidence Calibration)
        confidence = assessment.get("confidence", 0.8)
        
        # Thiếu bằng chứng -> Không thể tự tin
        if not evidence_refs:
            confidence = min(confidence, 0.2)
            assessment["primary_issue"] = "insufficient_evidence"
            
        # Tồn tại dữ liệu xung đột (data conflicts) -> Trừ 20% độ tự tin
        if data_conflicts:
            confidence *= 0.8
            
        # Chuẩn hóa giới hạn [0.0 - 1.0]
        confidence = max(0.0, min(1.0, round(confidence, 2)))
        assessment["confidence"] = confidence
        
        # 5. Phát ra sự kiện hoàn thành (Lifecycle)
>>>>>>> 0fd2fda423711fdf0f24264a8859d30a024c2485
        self.trace.emit(
            case_id=case_id,
            event_type="verification_completed",
            actor="verifier",
<<<<<<< HEAD
            decision_code=output["assessment"]["primary_issue"],
            evidence_refs=output["evidence_refs"][:20],
            attributes={
                "confidence": output["assessment"]["confidence"],
                "case_status": output["assessment"]["case_status"],
            },
        )
        return output
=======
            attributes={
                "calibrated_confidence": confidence,
                "conflicts_detected": len(data_conflicts)
            }
        )
        
        # 6. Ráp thành Output chuẩn
        return {
            "schema_version": "day09-l3a-output-v2",
            "case_id": case_id,
            "assessment": assessment,
            "affected_entities": affected_entities,
            "claim_assessments": finance.get("claim_assessments", []),
            "root_cause_analysis": root_cause_analysis,
            "evidence_refs": evidence_refs,
            "data_conflicts": data_conflicts,
            "financial_resolution": financial_resolution,
            "resolution_actions": resolution_actions
        }

>>>>>>> 0fd2fda423711fdf0f24264a8859d30a024c2485
