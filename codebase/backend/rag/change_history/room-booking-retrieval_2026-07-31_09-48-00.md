# Fix room booking retrieval

- Thời gian: `2026-07-31 09:48:00 +07:00`
- Branch: `master_B1_E402`
- Commit triển khai: `b3cca008ac5a8296edd4d7b40fbe06fd6b619bed`
- Commit chứa logic cũ: `be441dcf8380e213ae737850a3c48d87e6e1f6c6`

## Logic cũ

- Câu hỏi “Cách đặt phòng trong thư viện như thế nào?” phải gọi LLM router.
- OpenAI router có thể trả `help`, `unsupported_action` hoặc `factual` cho cùng
  một kiểu câu hỏi, khiến pipeline đôi lúc dừng trước retrieval.
- Khi một chunk xuất hiện trong nhiều BM25 query variants, retriever giữ kết
  quả đầu tiên. Điểm cao hơn từ query rewrite bị bỏ.
- Chunk hướng dẫn Outlook đứng ngoài top-k nên generator chỉ nhận các chunk
  chính sách đặt phòng.

## Logic mới

- Câu hỏi hỏi cách tự đặt phòng được fast-route thành `factual` và dùng
  deterministic search query về Microsoft Outlook.
- Yêu cầu bot đặt hoặc hủy phòng hộ người dùng được fast-route thành
  `unsupported_action`.
- BM25 merge giữ điểm cao nhất của mỗi `chunk_id` qua tất cả query variants.
- Chunk `huong-dan-dat-phong-bang-microsoft-outlook` lên top-1 cho câu hỏi
  hướng dẫn đặt phòng.

## File thay đổi

- `codebase/backend/rag/router.py`
- `codebase/backend/rag/retriever.py`
- `codebase/backend/tests/test_router.py`
- `codebase/backend/tests/test_retrieval.py`
- `codebase/backend/tests/test_retrieval_robustness.py`

## Verify

- TDD RED: 3 regression tests fail đúng tại procedural routing, lexical
  max-score merge và Outlook top-k.
- TDD GREEN: 3 regression tests pass.
- Toàn bộ backend: `85 passed in 11.18s`.
- `python -m compileall -q backend/rag backend/tests`: thành công.
- Smoke test `/ask` bằng OpenAI API key thật:
  - HTTP `200`, intent `factual`, `has_evidence=true`.
  - Câu trả lời có Outlook, Calendar, New Meeting, Rooms và Send.
  - Source chính là chunk hướng dẫn đặt phòng Outlook.

## Artifact

Không cần ingest hoặc rebuild index. Bản sửa chỉ thay routing online và cách
merge kết quả BM25 đã có.

## Khôi phục

```powershell
git revert b3cca008ac5a8296edd4d7b40fbe06fd6b619bed

# Áp dụng lại trên branch khác
git cherry-pick b3cca008ac5a8296edd4d7b40fbe06fd6b619bed
```
