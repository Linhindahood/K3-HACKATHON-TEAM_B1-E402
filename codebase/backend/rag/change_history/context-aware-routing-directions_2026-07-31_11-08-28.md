# Context-aware routing and direction origin

- Thời gian: `2026-07-31 11:08:28` (Asia/Saigon)
- Branch: `master_B1_E402`
- Commit: chưa commit theo rule “thay đổi nhỏ không nên commit”
- Phạm vi: chỉ RAG router, direction parser và regression tests

## Lỗi cũ

- Các câu hỏi hướng dẫn đặt phòng bị fast-route bằng danh sách keyword cứng.
- Câu dùng từ “book phòng” có thể bị LLM phân loại thành `help`, làm pipeline
  dừng trước retrieval và thiếu toàn bộ context tài liệu.
- Direction parser chỉ đọc `search_query` và chỉ hiểu dạng `từ A đến B`.
  Khi câu hỏi ghi `từ tòa E tôi muốn tìm...`, `đi từ tòa E, ...` hoặc
  `xuất phát tại tòa E`, parser mặc định sai về Cổng chính.

## Logic mới

- Bỏ fast-route cho các mẫu hỏi hướng dẫn. Câu hỏi cụ thể được LLM làm sạch
  query rồi tiếp tục retrieval.
- `help` chỉ fast-route với câu hỏi rõ ràng về chức năng/cách dùng bot. Nếu LLM
  trả `help` cho một câu có context cụ thể, router fail-open thành `factual` và
  giữ câu đã normalize làm `search_query`.
- Chỉ giữ rule từ chối cho yêu cầu đặt/book phòng thay người dùng có tín hiệu
  ủy quyền rõ như `bạn/bot`, `giúp tôi`, `hộ mình`.
- Direction parser lấy origin rõ ràng từ câu gốc trước, sau đó mới dùng
  destination trong query rewrite. Chỉ mặc định Cổng chính khi câu gốc không
  nêu origin.

## Kiểm chứng

- RED trước sửa: `9 failed, 11 passed`.
- Regression tests sau sửa: `20 passed`.
- Toàn bộ backend tests, cô lập dependency trong `codebase/.venv`:
  `99 passed in 11.48s`.
- Router API thật cho câu nhóm 20 người:
  `intent=factual`, `search_query=phòng họp 20 người hướng dẫn đặt phòng`.
- Smoke test pipeline thật trả hướng dẫn Outlook, `has_evidence=true` và hai
  nguồn tài liệu đặt phòng.
- Hai câu chỉ đường trong log đều parse origin thành `tòa E`.

## File thay đổi

- `backend/rag/router.py`
- `backend/rag/directions.py`
- `backend/tests/test_router.py`
- `backend/tests/test_directions.py`

## Cách quay lại logic cũ

Chỉ revert bốn file ở trên từ diff của task này. Không đụng các thay đổi đang
có sẵn trong `multimodal.py`, `source_registry.py`, `test_multimodal.py`,
`.gitignore` hoặc thư mục `bot/`.

Sau rollback, chạy:

```powershell
pytest backend/tests/test_router.py backend/tests/test_directions.py -q
```

Các regression test mới sẽ fail và tái hiện chính xác hai lỗi cũ.
