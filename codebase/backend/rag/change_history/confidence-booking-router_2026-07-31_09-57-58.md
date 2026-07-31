# Confidence-based room booking router

- Thời gian: `2026-07-31 09:57:58 +07:00`
- Branch: `master_B1_E402`
- Commit triển khai: `029531c5b216e208b49bc7ea1dada943c159a40a`
- Commit chứa logic cũ: `b3cca008ac5a8296edd4d7b40fbe06fd6b619bed`

## Logic cũ

- Regex hỏi cách đặt phòng tìm keyword ở bất kỳ vị trí nào trong câu.
- Câu “làm sao để bạn đặt phòng A101 giúp tôi” bị ép thành `factual`.
- Câu ủy quyền có từ lịch sự ở đầu hoặc không dấu có thể lọt sang LLM và bị
  phân loại không ổn định.

## Logic mới

- Fast-route chỉ chạy khi câu có chủ đề `đặt phòng` hoặc `dat phong`.
- Tín hiệu ủy quyền rõ như `bạn/bot đặt phòng` hoặc `đặt phòng ... giúp/hộ tôi`
  được ưu tiên thành `unsupported_action`.
- Tín hiệu tra cứu rõ như `tra xem`, `hướng dẫn`, `chỉ cách`, `làm sao`,
  `quy trình` được route thành `factual`.
- Câu không có tín hiệu chắc chắn như `đặt phòng A101` không bị hard-code và
  tiếp tục chuyển cho LLM router.

## Bộ câu hỏi lắt léo

Nhóm `factual`:

- `làm ơn giúp tôi tra xem làm sao để đặt phòng thư viện`
- `Bạn có thể chỉ tôi cách tự đặt phòng thư viện không?`
- `Nhờ bạn hướng dẫn quy trình đặt phòng A102 cho tôi`
- `lam on chi toi cach dat phong thu vien`

Nhóm `unsupported_action`:

- `làm sao để bạn đặt phòng A101 giúp tôi`
- `làm ơn đặt phòng A101 giúp tôi`
- `nhờ bot đặt phòng A102 hộ mình`
- `lam on dat phong A103 giup toi`

Nhóm chuyển LLM:

- `đặt phòng A101`

## File thay đổi

- `codebase/backend/rag/router.py`
- `codebase/backend/tests/test_router.py`

## Verify

- TDD RED: `5 failed, 9 passed`; fail đúng ở câu không dấu và câu ủy quyền
  lịch sự/lắt léo.
- Router tests sau sửa: `14 passed`.
- Toàn bộ backend: `95 passed in 11.48s`.
- `python -m compileall -q backend/rag backend/tests`: thành công.
- Smoke test `/ask` bằng API key thật:
  - Câu tra cứu lịch sự: `factual`, có evidence và có hướng dẫn Outlook.
  - Câu yêu cầu bot đặt hộ: `unsupported_action`, không chạy retrieval.

## Artifact

Không cần ingest hoặc rebuild index.

## Khôi phục

```powershell
git revert 029531c5b216e208b49bc7ea1dada943c159a40a

# Áp dụng lại trên branch khác
git cherry-pick 029531c5b216e208b49bc7ea1dada943c159a40a
```
