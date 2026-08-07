"""Persistence tối giản bằng JSONL cho bản mock (ticket, handover).

Vì sao JSONL: rule `*.jsonl` trong codebase/.gitignore tự động loại các file này khỏi git, nên
dữ liệu demo không bao giờ lỡ bị commit. Ghi đè toàn file khi update — số lượng bản ghi trong
demo rất nhỏ nên không cần append-log phức tạp.

Không import streamlit ở đây để module thuần Python, unit-test được.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from config import local_store_dir


def _path(filename: str) -> Path:
    return local_store_dir() / filename


def read_all(filename: str) -> list[dict[str, Any]]:
    """Đọc toàn bộ bản ghi. File chưa tồn tại -> [] (trường hợp chạy lần đầu, không phải lỗi).

    Dòng hỏng bị bỏ qua thay vì làm sập cả trang: dữ liệu demo không đáng để đánh đổi UX.
    """
    path = _path(filename)
    if not path.is_file():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def write_all(filename: str, records: list[dict[str, Any]]) -> None:
    """Ghi đè toàn bộ file theo kiểu atomic (ghi file tạm rồi replace) để tiến trình Streamlit
    bị kill giữa chừng không để lại file JSONL cụt."""
    directory = local_store_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = _path(filename)

    fd, tmp_name = tempfile.mkstemp(dir=str(directory), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for record in records:
                # ensure_ascii=False để tiếng Việt lưu nguyên vẹn, dễ debug bằng mắt.
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def append(filename: str, record: dict[str, Any]) -> None:
    """Thêm 1 bản ghi vào cuối file."""
    directory = local_store_dir()
    directory.mkdir(parents=True, exist_ok=True)
    with _path(filename).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
