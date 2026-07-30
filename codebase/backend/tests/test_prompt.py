"""Tests for the centralized grounded prompt."""
from __future__ import annotations

from backend.rag.prompt import SYSTEM_PROMPT, build_user_prompt


def test_prompt_contains_source_boundaries_and_booking_limit():
    prompt = build_user_prompt(
        "Hãy đặt phòng A102 giúp tôi",
        [{"source": "library#a102", "text": "Cách đặt phòng bằng Outlook."}],
    )

    assert "[S1]" in prompt
    assert "Nguồn: library#a102" in prompt
    assert "Cách đặt phòng bằng Outlook." in prompt
    assert "marker nguồn tương ứng" in SYSTEM_PROMPT
    assert "chỉ hướng dẫn quy trình" in SYSTEM_PROMPT
    assert "không tuyên bố đã thực hiện" in SYSTEM_PROMPT
