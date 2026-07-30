# CLAUDE.md — VinAI Discord Bot (hackathon 36h)

> Đọc file này trước khi động vào code. Nội dung đầy đủ nằm ở `docs/skills.md` (quy tắc làm việc),
> `docs/Requirement.md` (scope sản phẩm), `docs/Architecture.md` (kiến trúc kỹ thuật + phân công).

## Dự án là gì

Chatbot Discord hỗ trợ sinh viên khoá VinAI thực chiến tra cứu **nội quy**, **tiện ích**,
**vị trí cơ sở vật chất** — dùng RAG. Chi tiết đầy đủ: `docs/Requirement.md`.

## Cấu trúc repo

- Toàn bộ code nằm trong `codebase/` (đây là cấu trúc nộp bài BTC yêu cầu — xem
  `asserts/architecture.png` và mục "Nộp bài" trong `README.md` gốc).
- Bên trong `codebase/`: `backend/` (FastAPI — lõi RAG), `bot/` (Discord client), `frontend/`
  (Streamlit — UI debug nội bộ, không phải sản phẩm cuối). Cả `bot/` và `frontend/` đều gọi
  vào `backend/` qua HTTP (`POST /ask`), không tự chứa logic RAG riêng.
- Chi tiết từng thư mục, ai sở hữu file nào: `docs/Architecture.md`.

## Nguyên tắc số 1: Scope đã chốt là luật

Trước khi thêm tính năng mới, tự hỏi: *việc này có nằm trong "Trong phạm vi" của
`docs/Requirement.md` không?* Đặc biệt: bot **không** tự thực hiện đặt lịch/book phòng thật —
chỉ trả lời bằng text hướng dẫn quy trình. Phát sinh ý tưởng mới → không tự thêm, cả team đồng ý
và cập nhật `docs/Requirement.md` trước.

## Vai trò chuẩn hoá (dùng để đặt tên branch & commit)

`data` (tổng hợp/làm sạch knowledge base) · `prompt` (viết prompt, RAG pipeline) ·
`build` (code bot/backend/frontend, tích hợp) · `spec` (giữ scope, tài liệu, điều phối) ·
`qa` (test, validation với người dùng thật).

## Branch & commit

- Branch: `<role>/<ten-chuc-nang-khong-dau-cach-bang-gach-ngang>` (vd `build/discord-bot-skeleton`).
  Không đặt tên chung chung như `fix`, `update`.
- Commit: `Tên thành viên - Role - Tên chức năng` (vd `Trang - Build - Setup khung bot Discord`).
  1 commit = 1 thay đổi có ý nghĩa. Sửa lỗi cho phần người khác → ghi role/chức năng gốc, không
  ghi tên người sửa thay tên chủ sở hữu.

## Quy trình push/merge

Tạo branch từ `main` → commit + push thường xuyên → tự test nhanh trước khi merge vào `main`,
báo 1 dòng trong group chat khi merge → conflict thì người tạo ra tự xử lý → `main` luôn phải
chạy được (demo-ready), không push code lỗi vào `main` kể cả gần deadline.

Toàn văn quy tắc (checklist trước khi mở branch, ví dụ chi tiết): `docs/skills.md`.
