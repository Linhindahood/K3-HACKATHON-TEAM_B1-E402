"""Tests for response policy and leak stripping in RAG V1."""
from __future__ import annotations

from backend.rag.response_policy import (
    GREETING_RESPONSE,
    HELP_RESPONSE,
    IDENTITY_RESPONSE,
    NO_EVIDENCE_ANSWER,
    UNSUPPORTED_ACTION_RESPONSE,
    get_deterministic_response,
    strip_internal_leakage,
)
from backend.rag.router import Intent


def test_deterministic_responses():
    greeting = get_deterministic_response(Intent.GREETING)
    assert greeting["answer"] == GREETING_RESPONSE
    assert greeting["has_evidence"] is False
    assert greeting["sources"] == []

    identity = get_deterministic_response(Intent.IDENTITY)
    assert identity["answer"] == IDENTITY_RESPONSE
    assert identity["has_evidence"] is False

    help_res = get_deterministic_response(Intent.HELP)
    assert help_res["answer"] == HELP_RESPONSE

    unsupported = get_deterministic_response(Intent.UNSUPPORTED_ACTION)
    assert unsupported["answer"] == UNSUPPORTED_ACTION_RESPONSE
    assert "không thể trực tiếp thực hiện" in unsupported["answer"]

    out_of_scope = get_deterministic_response(Intent.OUT_OF_SCOPE)
    assert out_of_scope["has_evidence"] is False
    assert "nằm ngoài dữ liệu" in out_of_scope["answer"]



def test_refusal_answers_use_friendly_tone():
    assert "mình" in NO_EVIDENCE_ANSWER.lower() or "bạn" in NO_EVIDENCE_ANSWER.lower()


def test_strip_internal_leakage_removes_markers_and_filenames():
    raw_output = "Đây là thông tin nội quy. [S1] Tham khảo thêm tại 2_Handbook_AI_IN_ACTION.txt#heading."
    cleaned = strip_internal_leakage(raw_output)
    assert "[S1]" not in cleaned
    assert "2_Handbook_AI_IN_ACTION.txt" not in cleaned
    assert "Đây là thông tin nội quy." in cleaned
