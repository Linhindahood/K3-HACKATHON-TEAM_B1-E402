"""Test vòng đời ticket + routing + persistence JSONL."""
from __future__ import annotations

import pytest

from services import mock_impl
from services.models import (
    PRIORITY_HIGH,
    PRIORITY_URGENT,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_RESOLVED,
    STATUS_WAITING,
    HandoverDraft,
    TicketDraft,
)


def _draft(**overrides) -> TicketDraft:
    data = {
        "subject": "Không đăng ký được môn Machine Learning",
        "category": "hoc_vu",
        "description": "Hệ thống báo lỗi prerequisite not satisfied.",
        "student_id": "SV2026001",
    }
    data.update(overrides)
    return TicketDraft(**data)


def test_tao_ticket_sinh_id_va_trang_thai_open():
    result = mock_impl.create_ticket(_draft())
    assert result.ok
    assert result.data.ticket_id.startswith("TK-")
    assert result.data.status == STATUS_OPEN


def test_routing_suy_department_tu_category():
    assert mock_impl.create_ticket(_draft(category="hoc_vu")).data.department == "Phòng Đào tạo"
    assert mock_impl.create_ticket(_draft(category="ky_thuat")).data.department == "Phòng CNTT"
    assert mock_impl.create_ticket(_draft(category="noi_quy")).data.department == "Phòng Công tác Sinh viên"


def test_category_la_gi_do_khong_biet_thi_ve_department_mac_dinh():
    ticket = mock_impl.create_ticket(_draft(category="khong_ton_tai")).data
    assert ticket.department == "Trung tâm Hỗ trợ Sinh viên"


@pytest.mark.parametrize("field", ["subject", "description"])
def test_thieu_truong_bat_buoc_thi_khong_tao_ticket(field):
    result = mock_impl.create_ticket(_draft(**{field: "   "}))
    assert not result.ok
    assert result.error
    # Quan trọng: không được tạo ticket rỗng khi validate fail.
    assert mock_impl.list_tickets().data == []


def test_ticket_luu_xuong_file_va_doc_lai_duoc():
    created = mock_impl.create_ticket(_draft()).data
    listed = mock_impl.list_tickets().data
    assert [t.ticket_id for t in listed] == [created.ticket_id]
    assert mock_impl.get_ticket(created.ticket_id).data.subject == created.subject


def test_get_ticket_khong_ton_tai_tra_loi_ro_rang():
    result = mock_impl.get_ticket("TK-KHONG-CO")
    assert not result.ok
    assert "Không tìm thấy" in result.error


def test_chuyen_trang_thai_hop_le_ghi_lai_su_kien():
    ticket = mock_impl.create_ticket(_draft()).data
    result = mock_impl.update_ticket_status(ticket.ticket_id, STATUS_IN_PROGRESS)
    assert result.ok
    assert result.data.status == STATUS_IN_PROGRESS
    assert len(result.data.events) == 2  # created + status_changed


def test_chan_buoc_nhay_trang_thai_khong_hop_le():
    ticket = mock_impl.create_ticket(_draft()).data
    result = mock_impl.update_ticket_status(ticket.ticket_id, STATUS_RESOLVED)
    assert not result.ok
    assert mock_impl.get_ticket(ticket.ticket_id).data.status == STATUS_OPEN


def test_ticket_da_dong_thi_khong_chuyen_duoc_nua():
    ticket = mock_impl.create_ticket(_draft()).data
    mock_impl.update_ticket_status(ticket.ticket_id, STATUS_CLOSED)
    result = mock_impl.update_ticket_status(ticket.ticket_id, STATUS_IN_PROGRESS)
    assert not result.ok


def test_vong_doi_day_du_open_den_closed():
    ticket = mock_impl.create_ticket(_draft()).data
    for status in (STATUS_IN_PROGRESS, STATUS_WAITING, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED):
        result = mock_impl.update_ticket_status(ticket.ticket_id, status)
        assert result.ok, f"không chuyển được sang {status}"
    assert mock_impl.get_ticket(ticket.ticket_id).data.status == STATUS_CLOSED


def test_loc_ticket_theo_trang_thai():
    a = mock_impl.create_ticket(_draft(subject="A")).data
    mock_impl.create_ticket(_draft(subject="B"))
    mock_impl.update_ticket_status(a.ticket_id, STATUS_IN_PROGRESS)
    assert len(mock_impl.list_tickets(status=STATUS_OPEN).data) == 1
    assert len(mock_impl.list_tickets(status=STATUS_IN_PROGRESS).data) == 1


def test_prefill_tu_chat_duoc_luu_kem_ticket():
    draft = _draft(
        source_question="Em không đăng ký được môn ML",
        source_answer="Mình chưa tìm thấy thông tin.",
        source_intent="factual",
        has_evidence=False,
        source_refs=["handbook.txt#quy-dinh"],
    )
    ticket = mock_impl.create_ticket(draft).data
    reloaded = mock_impl.get_ticket(ticket.ticket_id).data
    assert reloaded.source_question == draft.source_question
    assert reloaded.source_refs == draft.source_refs
    assert reloaded.has_evidence is False


def test_tieng_viet_khong_bi_hong_khi_luu_file():
    ticket = mock_impl.create_ticket(_draft(subject="Bảo lưu kết quả học tập")).data
    assert mock_impl.get_ticket(ticket.ticket_id).data.subject == "Bảo lưu kết quả học tập"


def test_suggest_priority():
    assert mock_impl.suggest_priority(urgent=True) == PRIORITY_URGENT
    assert mock_impl.suggest_priority(sensitive=True) == PRIORITY_HIGH
    assert mock_impl.suggest_priority() == "NORMAL"


def test_handover_luu_va_doc_lai_duoc():
    result = mock_impl.request_handover(
        HandoverDraft(question="Em muốn gặp nhân viên", reason_code="user_request", severity="HIGH")
    )
    assert result.ok
    assert result.data.handover_id.startswith("HO-")
    assert result.data.status == "WAITING_FOR_STAFF"
    assert len(mock_impl.list_handovers().data) == 1


def test_lich_hoc_demo_co_du_thong_tin():
    from datetime import date

    result = mock_impl.get_schedule("SV2026001", date(2026, 8, 10), date(2026, 8, 14))
    assert result.ok
    assert result.data
    first = result.data[0]
    assert first.subject and first.room and first.lecturer
    assert first.is_demo is True


def test_lich_hoc_cuoi_tuan_rong():
    from datetime import date

    result = mock_impl.get_schedule("SV2026001", date(2026, 8, 15), date(2026, 8, 16))
    assert result.ok
    assert result.data == []
