from backend.rag import generator


def test_generate_returns_fallback_for_empty_passages():
    result = generator.generate("giờ vào học là mấy giờ?", [])

    assert result["has_evidence"] is False
    assert result["sources"] == []
    assert "không tìm thấy thông tin" in result["answer"].lower()


def test_generate_uses_passages_when_evidence_is_strong_enough():
    passages = [
        {
            "text": "Sinh viên cần mặc đồng phục đúng quy định của khóa học.",
            "source": "noi_quy.md#trang-phuc",
            "score": 0.82,
        }
    ]

    result = generator.generate("trang phục thế nào?", passages)

    assert result["has_evidence"] is True
    assert result["sources"] == ["noi_quy.md#trang-phuc"]
    assert "đồng phục" in result["answer"].lower()
