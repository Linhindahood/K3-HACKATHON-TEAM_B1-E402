"""Điểm hoán đổi mock <-> API thật.

View LUÔN gọi qua `get_services()`, không import trực tiếp mock_impl/http_impl. Nhờ vậy khi
backend có endpoint thật, đổi USE_MOCK_SERVICES=0 là xong — không sửa dòng UI nào.
"""
from __future__ import annotations

from types import ModuleType
from typing import NamedTuple

from config import USE_MOCK_SERVICES


class Services(NamedTuple):
    """Bó các module service lại. Dùng module thay vì class vì các impl đều là hàm thuần,
    không có state riêng — state nằm ở file JSONL / backend."""

    tickets: ModuleType
    schedule: ModuleType
    profile: ModuleType
    handover: ModuleType
    using_mock: bool


def get_services() -> Services:
    """Trả về bộ service đang hoạt động.

    Không cache bằng st.cache_resource: hàm này chỉ import module (rất rẻ), và cache sẽ làm
    test khó override cờ USE_MOCK_SERVICES.
    """
    if USE_MOCK_SERVICES:
        from services import mock_impl as impl
    else:
        from services import http_impl as impl  # type: ignore[no-redef]

    return Services(
        tickets=impl,
        schedule=impl,
        profile=impl,
        handover=impl,
        using_mock=USE_MOCK_SERVICES,
    )
