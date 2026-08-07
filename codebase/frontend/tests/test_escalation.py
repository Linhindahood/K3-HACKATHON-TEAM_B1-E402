"""Test heuristic đề xuất handover.

Trọng tâm là CHỐNG BÁO ĐỘNG GIẢ: câu hỏi tra cứu bình thường có chứa từ nhạy cảm không được
bị đẩy lên mức cao, và từ khóa không được khớp nhầm giữa các từ khác nhau ("kỹ thuật" vs
"kỷ luật").
"""
from __future__ import annotations

from services import escalation
from services.models import SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_NONE


def test_grounded_factual_answer_khong_de_xuat_handover():
    result = escalation.assess("Quy định điểm danh thế nào?", intent="factual", has_evidence=True)
    assert result.severity == SEVERITY_NONE
    assert not result.should_offer


def test_greeting_khong_de_xuat_handover():
    assert escalation.assess("Xin chào", intent="greeting").severity == SEVERITY_NONE


def test_khong_co_evidence_thi_de_xuat_muc_trung_binh():
    result = escalation.assess("Học phí kỳ này bao nhiêu?", intent="factual", has_evidence=False)
    assert result.severity == SEVERITY_MEDIUM
    assert result.reason_code == escalation.REASON_NO_EVIDENCE


def test_loi_backend_thi_de_xuat_muc_cao():
    result = escalation.assess("Câu hỏi bất kỳ", error="⚠️ Không thể kết nối")
    assert result.severity == SEVERITY_HIGH
    assert result.reason_code == escalation.REASON_BACKEND_ERROR


def test_tu_khoa_khan_cap_len_muc_cao():
    result = escalation.assess("Em cần xử lý khẩn cấp việc này", intent="factual", has_evidence=True)
    assert result.severity == SEVERITY_HIGH
    assert result.reason_code == escalation.REASON_URGENT_KEYWORD


def test_ca_nhay_cam_khong_co_nguon_len_muc_cao():
    result = escalation.assess("Em muốn khiếu nại quyết định kỷ luật", intent="factual", has_evidence=False)
    assert result.severity == SEVERITY_HIGH
    assert result.reason_code == escalation.REASON_SENSITIVE_KEYWORD


def test_cau_hoi_tra_cuu_ve_ky_luat_chi_o_muc_trung_binh():
    """'Quy định kỷ luật là gì?' là câu hỏi thông tin, không phải ca kỷ luật cá nhân —
    có nguồn thì chỉ gợi ý nhẹ, không đẩy lên mức cao."""
    result = escalation.assess("Quy định kỷ luật của trường là gì?", intent="factual", has_evidence=True)
    assert result.severity == SEVERITY_MEDIUM


def test_khong_khop_nham_ky_thuat_voi_ky_luat():
    """Dấu tiếng Việt phải phân biệt được 'kỹ thuật' và 'kỷ luật'."""
    result = escalation.assess("Em gặp lỗi kỹ thuật khi đăng nhập", intent="factual", has_evidence=True)
    assert result.reason_code != escalation.REASON_SENSITIVE_KEYWORD


def test_unsupported_action_len_muc_cao():
    result = escalation.assess("Đặt giúp em phòng A101", intent="unsupported_action", has_evidence=False)
    assert result.severity == SEVERITY_HIGH
    assert result.reason_code == escalation.REASON_UNSUPPORTED_ACTION


def test_out_of_scope_o_muc_trung_binh():
    result = escalation.assess("Giá bitcoin hôm nay?", intent="out_of_scope", has_evidence=False)
    assert result.severity == SEVERITY_MEDIUM


def test_user_chu_dong_yeu_cau_luon_hop_le():
    result = escalation.user_requested()
    assert result.severity == SEVERITY_HIGH
    assert result.reason_code == escalation.REASON_USER_REQUEST
    assert result.should_offer


def test_llm_fail_du_co_tai_lieu_van_de_xuat_ho_tro():
    """Backend tìm được tài liệu (has_evidence=True) nhưng LLM không sinh được câu trả lời —
    sinh viên không nhận được gì hữu ích nên phải chủ động đề nghị hỗ trợ."""
    result = escalation.assess(
        "Quy định điểm danh?",
        intent="factual",
        has_evidence=True,
        answer="Mình đã tìm thấy tài liệu liên quan nhưng hiện chưa thể tạo câu trả lời. Bạn vui lòng thử lại sau nhé.",
    )
    assert result.severity == SEVERITY_HIGH
    assert result.reason_code == escalation.REASON_GENERATION_FAILED


def test_cau_tra_loi_binh_thuong_khong_bi_nham_la_loi_sinh():
    result = escalation.assess(
        "Quy định điểm danh?",
        intent="factual",
        has_evidence=True,
        answer="Sinh viên cần tham dự tối thiểu 80% số buổi học.",
    )
    assert result.severity == SEVERITY_NONE


def test_moi_escalation_deu_co_message_hien_thi():
    result = escalation.assess("Em muốn khiếu nại", intent="factual", has_evidence=False)
    assert result.message
    assert "không chắc chắn" not in result.message.lower()
