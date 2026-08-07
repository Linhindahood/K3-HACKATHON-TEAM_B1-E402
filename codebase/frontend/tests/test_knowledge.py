"""Test tầng đọc kho tri thức thật (chunks.jsonl).

KB là file tự sinh + gitignored nên có thể vắng mặt -> test phải chạy được cả 2 trường hợp.
"""
from __future__ import annotations

import json

import pytest

from services import knowledge


@pytest.fixture(autouse=True)
def clear_cache():
    """st.cache_data giữ kết quả giữa các test -> phải xóa, nếu không test sau đọc dữ liệu cũ."""
    knowledge.load_entries.clear()
    yield
    knowledge.load_entries.clear()


@pytest.fixture
def fake_kb(tmp_path, monkeypatch):
    """Dựng chunks.jsonl giả đúng schema thật (heading_path/text/source/source_url)."""
    path = tmp_path / "chunks.jsonl"
    rows = [
        {"heading_path": ["CÂU HỎI THƯỜNG GẶP"], "text": "VII. CÂU HỎI THƯỜNG GẶP", "source": "hb.txt", "source_url": "https://x"},
        {"heading_path": ["CÂU HỎI THƯỜNG GẶP", "Chương trình dạy trực tiếp hay online?"], "text": "Học viên học trực tiếp.", "source": "hb.txt", "source_url": "https://x"},
        {"heading_path": ["CÂU HỎI THƯỜNG GẶP", "Có được học lại không?"], "text": "Không nằm trong nội dung.", "source": "hb.txt", "source_url": "https://x"},
        {"heading_path": ["QUY ĐỊNH ĐÀO TẠO", "Điểm danh"], "text": "Tham dự tối thiểu 80% số buổi.", "source": "hb.txt", "source_url": "https://y"},
        {"heading_path": ["CÁC DỊCH VỤ TIỆN ÍCH", "Thư viện"], "text": "Thư viện mở cửa 8h-22h.", "source": "hb.txt", "source_url": "https://z"},
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    monkeypatch.setattr(knowledge, "KB_CHUNKS_PATH", path)
    return path


def test_kb_vang_mat_thi_tra_rong_khong_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "KB_CHUNKS_PATH", tmp_path / "khong-ton-tai.jsonl")
    assert knowledge.load_entries() == []
    assert knowledge.is_available() is False
    assert knowledge.get_entries() == []
    assert knowledge.list_groups() == []


def test_doc_duoc_kb_that(fake_kb):
    assert knowledge.is_available() is True
    assert len(knowledge.load_entries()) == 5


def test_gom_nhom_va_faq_dung_dau(fake_kb):
    groups = knowledge.list_groups()
    assert groups[0][0] == knowledge.FAQ_GROUP
    assert dict(groups)["QUY ĐỊNH ĐÀO TẠO"] == 1


def test_faq_loc_bo_chunk_tieu_de_khong_phai_cau_hoi(fake_kb):
    """Chunk chỉ có 1 cấp heading là tiêu đề mục, không phải cặp hỏi–đáp."""
    faq = knowledge.get_faq()
    assert len(faq) == 2
    assert all(entry.title.endswith("?") for entry in faq)


def test_search_khong_dau_van_tim_duoc(fake_kb):
    assert knowledge.get_entries(query="diem danh")
    assert knowledge.get_entries(query="điểm danh")


def test_search_tim_trong_ca_noi_dung(fake_kb):
    results = knowledge.get_entries(query="80%")
    assert len(results) == 1
    assert results[0].title == "Điểm danh"


def test_loc_theo_nhom(fake_kb):
    results = knowledge.get_entries(group="CÁC DỊCH VỤ TIỆN ÍCH")
    assert len(results) == 1
    assert results[0].title == "Thư viện"


def test_moi_muc_deu_giu_source_url_de_trich_dan(fake_kb):
    assert all(entry.source_url for entry in knowledge.get_entries())


def test_dong_hong_bi_bo_qua_khong_lam_sap(tmp_path, monkeypatch):
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        '{"heading_path": ["A", "B"], "text": "ok", "source": "s", "source_url": "u"}\n'
        "{ dòng hỏng không phải json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(knowledge, "KB_CHUNKS_PATH", path)
    assert len(knowledge.load_entries()) == 1
