"""Tests for the centralized grounded prompt."""
from __future__ import annotations

from backend.rag.prompt import (
    ROUTE_DIRECTIONS_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_route_directions_prompt,
    build_user_prompt,
)
from backend.rag.route_graph import plan_route


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


def test_route_prompt_is_grounded_in_the_shared_route_plan_not_image_guessing():
    plan = plan_route("tòa E", "tòa A")

    prompt = build_route_directions_prompt(
        "Đi từ tòa E tới tòa A",
        plan,
    )

    assert "Tòa E" in prompt
    assert "Tòa A" in prompt
    assert all(step in prompt for step in plan.steps)
    assert "không thêm địa điểm" in ROUTE_DIRECTIONS_SYSTEM_PROMPT.casefold()
    assert "đọc ảnh" not in prompt.casefold()
