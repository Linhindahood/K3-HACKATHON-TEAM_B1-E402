# validation/ — Feedback log từ vòng user test

> Chấm theo `04-rubric.md` R6 (8 điểm): cần ≥5 mẩu feedback từ ≥5 người ngoài nhóm (có ≥2 willing
> user đã khai từ CP1), quote nguyên văn + tên/vai, và ≥1 thay đổi từ feedback ghi vào Changelog
> (hoặc giữ nguyên có lý do căn cứ).

## Trạng thái hiện tại

**Chưa có** — thư mục này chỉ mới được dựng khung, chưa có feedback log thật nào. Không tự bịa
quote/tên người dùng vào đây — rubric R1 và luật chung của sự kiện tính số liệu bị chỉnh sửa/che
giấu là **không được tính điểm**.

## Việc cần làm (role `qa`)

1. Xác nhận ≥3 người thật ngoài nhóm sẵn sàng thử (đã khai dự kiến từ CP1, theo `docs/Canvas.md`).
2. Cho họ thử bot qua Discord thật (xem `codebase/README.md` để setup) hoặc qua danh sách câu hỏi
   mẫu trong `codebase/backend/tests/sample_questions.md` / `eval/golden_set.jsonl`.
3. Ghi log — mỗi mẩu cần: tên/vai người thử, câu hỏi đã thử, quote nguyên văn phản hồi của họ,
   ngày giờ. Đề xuất format 1 file `feedback-log.md` trong thư mục này.
4. Với mỗi feedback: quyết định có sửa gì không → ghi vào `changelog.md` trong thư mục này (sửa gì
   + lý do, hoặc giữ nguyên + lý do căn cứ).
