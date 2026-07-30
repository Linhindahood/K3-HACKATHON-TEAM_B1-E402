# Route → pipeline delegation

- Thời gian: `2026-07-30 20:42:48 +07:00`
- Branch: `master_B1_E402`
- Commit triển khai: `<điền sau khi commit — git rev-parse HEAD>`
- Commit chứa logic cũ: `3403a710e72626acddf469ba9704540c7b9309e6` (Dat-Build-Add Chatbot log)

## Bối cảnh

Merge conflict giữa `cddf871` (Minh - add pipeline — `routes.py` gọi qua
`pipeline.answer_question`) và `3403a71` (Dat-Build-Add Chatbot log — `routes.py` gọi tay
`retriever.retrieve()` + `generator.generate()` kèm logging, nhánh này rẽ ra từ **trước** khi
Minh thêm `pipeline.py` nên không có phần đó) khi resolve đã giữ lại toàn bộ nội dung `3403a71`,
làm mất phần dùng `pipeline.py` của Minh. Hệ quả: `backend/tests/test_routes.py` (viết đúng theo
thiết kế `cddf871`) fail với `AttributeError: module 'backend.api.routes' has no attribute
'rag_pipeline'`.

## Logic cũ

- `routes.py` tự gọi `retriever.retrieve()` rồi `generator.generate()`, lặp lại logic đã có sẵn
  trong `pipeline.py` (2 nơi giữ cùng 1 logic, dễ lệch nhau khi 1 bên đổi mà bên kia không biết).
- `AskResponse` có thêm field `intent: str = "general"` — không nơi nào trong `bot/` (Node.js) hay
  `frontend/` (Streamlit) đọc field này; pipeline/generator cũng không tạo ra intent thật nào, giá
  trị luôn là hằng số `"general"`.

## Logic mới

- `routes.py` gọi `backend.rag.pipeline.answer_question()` (alias `rag_pipeline`, đúng thiết kế gốc
  của Minh ở `cddf871`) — khôi phục `pipeline.py` làm cổng vào RAG duy nhất (đúng bảng module trong
  `rag/ARCHITECTURE.md` §4.3.1), đồng thời giữ nguyên phần đo latency + `log_ask()` mà Đạt đã thêm.
- Bỏ field `intent` khỏi `AskResponse` (không dùng, không nơi nào tiêu thụ, không phản ánh logic
  thật nào của hệ thống).

## Verify

- `pytest backend/tests/` — trước: `1 failed` (`test_ask_route_returns_pipeline_contract`), sau:
  `49 passed`.
- Không đổi API contract bên ngoài (`answer`, `sources`, `has_evidence`) — `bot/` và `frontend/`
  không cần sửa gì thêm.

## File thay đổi

- `codebase/backend/api/routes.py`

## Khôi phục

```powershell
git status --short
git revert <commit triển khai>

# Áp dụng lại trên branch khác
git cherry-pick <commit triển khai>
```
