"""Test E2E toàn bộ vòng đời qua giao diện thật:
CHAT → RAG → TẠO TICKET → ĐỊNH TUYẾN → THEO DÕI → HANDOVER.

Dùng streamlit.testing.v1.AppTest để chạy chính app.py trong tiến trình test (không cần
trình duyệt, không cần backend). Backend RAG được monkeypatch ở tầng services.chat.
"""
from __future__ import annotations

import re

import pytest
from streamlit.testing.v1 import AppTest

from conftest import APP_PATH


@pytest.fixture
def app(monkeypatch, sample_ask_result):
    """App đã stub sẵn backend RAG và health check — mọi test bắt đầu từ trạng thái sạch."""
    import api_client
    from services import chat, knowledge

    monkeypatch.setattr(chat, "send_message", lambda q, **kw: sample_ask_result)
    monkeypatch.setattr(api_client, "check_health", lambda: {"status": "ok", "ready": True})
    knowledge.load_entries.clear()

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def _button(at, predicate):
    for btn in at.button:
        if predicate(btn.label):
            return btn
    raise AssertionError(f"Không tìm thấy nút. Hiện có: {[b.label for b in at.button]}")


def _all_markdown(at) -> str:
    return "\n".join(m.value for m in at.markdown)


# --- Regression: các chức năng cũ phải còn nguyên -------------------------
def test_app_khoi_dong_khong_loi(app):
    assert not app.exception


def test_dieu_huong_co_du_5_trang_chinh(app):
    options = app.radio[0].options
    for expected in ["💬 Chat", "📅 Lịch học", "🎫 Yêu cầu của tôi", "❓ FAQ & Tra cứu", "👤 Hồ sơ"]:
        assert expected in options


def test_man_hinh_chao_van_con_cau_hoi_goi_y(app):
    labels = [b.label for b in app.button]
    assert any("Nội quy chung" in label for label in labels)


def test_quick_action_hien_du_6_nut(app):
    labels = [b.label for b in app.button]
    for expected in ["📚 Học vụ", "📜 Nội quy & quy định", "📅 Lịch học", "📝 Dịch vụ sinh viên", "🎫 Yêu cầu hỗ trợ", "👨‍💼 Gặp nhân viên"]:
        assert expected in labels


def test_hoi_dap_hien_badge_va_citation(app):
    _button(app, lambda label: "Nội quy chung" in label).click().run()
    assert not app.exception
    markdown = _all_markdown(app)
    assert "c24-badge" in markdown
    assert "Có nguồn xác thực" in markdown
    assert any("Nguồn tham khảo (1)" in e.label for e in app.expander)


def test_xoa_lich_su_hoat_dong(app):
    _button(app, lambda label: "Nội quy chung" in label).click().run()
    assert len(app.session_state["messages"]) == 2
    _button(app, lambda label: "Xóa lịch sử" in label).click().run()
    assert app.session_state["messages"] == []


# --- Luồng chính: chat -> ticket -> tracking ------------------------------
def test_e2e_tu_cau_tra_loi_den_ticket_va_theo_doi(app):
    # 1. Hỏi -> AI trả lời
    _button(app, lambda label: "Nội quy chung" in label).click().run()
    assert not app.exception

    # 2. Bấm "Tạo yêu cầu hỗ trợ" ngay dưới câu trả lời -> nhảy sang trang Ticket
    app.button(key="tk_create_1").click().run()
    assert not app.exception
    assert app.session_state["nav"] == "🎫 Yêu cầu của tôi"
    assert app.session_state["ticket_draft"]["question"]

    # 3. Điền form, chọn danh mục Học vụ và gửi
    app.text_input[0].set_value("Không đăng ký được môn Machine Learning").run()
    app.text_area[0].set_value("Hệ thống báo lỗi prerequisite not satisfied.").run()
    app.selectbox[0].set_value("hoc_vu").run()
    _button(app, lambda label: "Gửi yêu cầu" in label).click().run()
    assert not app.exception

    # 4. Ticket ID được sinh và hiển thị
    ticket_id = app.session_state["selected_ticket_id"]
    assert re.match(r"TK-\d{8}-[0-9A-F]{4}", ticket_id)

    # 5. Trang chi tiết hiện trạng thái + phòng ban đã ĐỊNH TUYẾN theo danh mục
    markdown = _all_markdown(app)
    assert ticket_id in markdown
    assert "Mới tạo" in markdown
    assert "Phòng Đào tạo" in markdown

    # 6. Lịch sử chat KHÔNG bị mất khi chuyển trang
    assert len(app.session_state["messages"]) == 2


def test_ticket_luu_lai_va_hien_trong_danh_sach(app):
    from services import mock_impl
    from services.models import TicketDraft

    created = mock_impl.create_ticket(
        TicketDraft(subject="Xin giấy xác nhận sinh viên", category="dich_vu", description="Cần bản cứng.")
    ).data

    app.session_state["nav"] = "🎫 Yêu cầu của tôi"
    app.run()
    assert not app.exception
    markdown = _all_markdown(app)
    assert created.ticket_id in markdown
    assert "Phòng Dịch vụ Sinh viên" in markdown


def test_tien_trang_thai_ticket_qua_nut_demo(app):
    from services import mock_impl
    from services.models import STATUS_IN_PROGRESS, TicketDraft

    created = mock_impl.create_ticket(
        TicketDraft(subject="Lỗi đăng nhập portal", category="ky_thuat", description="Không vào được.")
    ).data

    app.session_state["nav"] = "🎫 Yêu cầu của tôi"
    app.session_state["selected_ticket_id"] = created.ticket_id
    app.run()
    _button(app, lambda label: "Mô phỏng xử lý" in label).click().run()
    assert not app.exception
    assert mock_impl.get_ticket(created.ticket_id).data.status == STATUS_IN_PROGRESS


# --- Handover -------------------------------------------------------------
def test_nut_gap_nhan_vien_tao_handover(app):
    _button(app, lambda label: "Nội quy chung" in label).click().run()
    app.button(key="tk_handover_1").click().run()
    assert not app.exception
    assert app.session_state["nav"] == "🎫 Yêu cầu của tôi"

    _button(app, lambda label: "Xác nhận chuyển" in label).click().run()
    assert not app.exception

    from services import mock_impl

    handovers = mock_impl.list_handovers().data
    assert len(handovers) == 1
    assert handovers[0].status == "WAITING_FOR_STAFF"
    assert "HO-" in _all_markdown(app)


def test_quick_action_gap_nhan_vien_hoat_dong_khi_chua_chat(app):
    _button(app, lambda label: "Gặp nhân viên" in label).click().run()
    assert not app.exception
    assert app.session_state["nav"] == "🎫 Yêu cầu của tôi"
    assert app.session_state["handover_ctx"]


def test_cau_hoi_khong_co_nguon_hien_goi_y_handover(monkeypatch, sample_ask_result):
    """Câu trả lời không có bằng chứng -> UI phải gợi ý tạo yêu cầu, không im lặng."""
    import api_client
    from api_client import AskResult
    from services import chat

    no_evidence = AskResult(answer="Mình chưa tìm thấy thông tin.", sources=[], has_evidence=False, intent="factual")
    monkeypatch.setattr(chat, "send_message", lambda q, **kw: no_evidence)
    monkeypatch.setattr(api_client, "check_health", lambda: {"status": "ok", "ready": True})

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _button(at, lambda label: "Nội quy chung" in label).click().run()
    assert not at.exception
    assert "chưa tìm thấy thông tin chính thức" in _all_markdown(at).lower()


def test_loi_backend_hien_error_state_va_khong_bia_cau_tra_loi(monkeypatch):
    import api_client
    from api_client import AskResult
    from services import chat

    failed = AskResult(error="⚠️ Không thể kết nối tới hệ thống. Vui lòng thử lại sau.")
    monkeypatch.setattr(chat, "send_message", lambda q, **kw: failed)
    monkeypatch.setattr(api_client, "check_health", lambda: {"status": "offline", "ready": False})

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _button(at, lambda label: "Nội quy chung" in label).click().run()
    assert not at.exception
    assert any("Không thể kết nối" in err.value for err in at.error)


# --- Các trang còn lại ----------------------------------------------------
@pytest.mark.parametrize(
    "page",
    ["📅 Lịch học", "🎫 Yêu cầu của tôi", "❓ FAQ & Tra cứu", "👤 Hồ sơ", "ℹ️ Giới thiệu"],
)
def test_moi_trang_render_khong_loi(app, page):
    app.session_state["nav"] = page
    app.run()
    assert not app.exception, [str(e.value) for e in app.exception]


def test_trang_lich_hoc_co_nhan_demo_va_thong_tin_buoi_hoc(app):
    app.session_state["nav"] = "📅 Lịch học"
    app.run()
    markdown = _all_markdown(app)
    assert "DEMO DATA" in markdown


def test_trang_ho_so_hien_thong_tin_va_dang_xuat(app):
    app.session_state["nav"] = "👤 Hồ sơ"
    app.run()
    markdown = _all_markdown(app)
    assert "SV2026001" in markdown
    assert "DEMO DATA" in markdown

    _button(app, lambda label: "Đăng xuất" in label).click().run()
    assert app.session_state["logged_in"] is False


def test_trang_faq_doc_kb_that_neu_da_ingest(app):
    from services import knowledge

    app.session_state["nav"] = "❓ FAQ & Tra cứu"
    app.run()
    assert not app.exception
    if knowledge.is_available():
        assert app.expander, "KB đã ingest thì phải hiển thị các mục kiến thức"
    else:
        assert "chưa sẵn sàng" in _all_markdown(app).lower()


def test_nhieu_luot_chat_khong_gay_trung_key_widget(app):
    """DuplicateWidgetID là lỗi hay gặp nhất khi mỗi câu trả lời có nút riêng."""
    for _ in range(3):
        app.chat_input[0].set_value("Quy định điểm danh?").run()
    assert not app.exception
    assert len(app.session_state["messages"]) == 6
