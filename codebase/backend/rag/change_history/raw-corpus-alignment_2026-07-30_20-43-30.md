# Raw corpus alignment với ingest.py

- Thời gian: `2026-07-30 20:43:30 +07:00`
- Branch: `master_B1_E402`
- Commit triển khai: `<điền sau khi commit — git rev-parse HEAD>`
- Commit chứa logic cũ: không áp dụng — đây là thiếu dữ liệu nguồn, không phải lỗi code.

## Bối cảnh

`backend/knowledge_base/raw/` chỉ có 3 file placeholder `.md` (`noi_quy.md`, `tien_ich.md`,
`vi_tri_co_so_vat_chat.md`, nội dung toàn `(TODO)`) từ lúc scaffold ban đầu của dự án — không khớp
6 tên file mà `ingest.py::_SOURCES`/`_source_inventory` cần: `1_map.jpg`,
`2_Handbook_AI_IN_ACTION.txt`, `3_link_vi_tri.txt`, `4_gio_mo_cua_library.txt`,
`5_ket_qua_khoa_1.txt`, `6_loai_phong_va_huong_dan_dat_phong.txt`. Hệ quả:
`load_raw_documents()` trả về rỗng trên máy chưa có 6 file thật, làm 5 case trong
`backend/tests/test_ingest.py` fail (`assert 0 == 1`, `assert []`...).

`backend/knowledge_base/processed/chunks.jsonl` (89 chunk) đã có sẵn và được commit — do Minh build
cục bộ với 6 file thật rồi commit artifact, nhưng bản thân 6 file raw chưa từng được commit (đúng
quy định bảo mật dữ liệu, xem README gốc mục "Bảo mật dữ liệu được cung cấp").

## Thay đổi

- Copy nguyên văn cả 6 file từ `data/docs/` vào `backend/knowledge_base/raw/` — **không sửa nội
  dung**, không suy đoán/bổ sung gì thêm.
- Thêm 6 dòng vào `.gitignore` (`codebase/backend/knowledge_base/raw/{1_map.jpg, 2_Handbook_AI_IN_ACTION.txt,
  3_link_vi_tri.txt, 4_gio_mo_cua_library.txt, 5_ket_qua_khoa_1.txt, 6_loai_phong_va_huong_dan_dat_phong.txt}`)
  — bắt buộc phải thêm cùng lúc, vì nếu không, copy 6 file thật vào đây sẽ vô tình đưa dữ liệu thật
  vào thư mục đang bị git track (`raw/` trước đó không hề có rule ignore riêng).

## Verify

- `pytest backend/tests/test_ingest.py` — trước: `5 failed`, sau: `5 passed`.
- Chạy thử `load_raw_documents()` + `chunk_documents()` từ 6 file vừa copy (không ghi artifact ra
  đĩa), so với `backend/knowledge_base/processed/chunks.jsonl` đã commit sẵn: **khớp 100% cả
  `chunk_id` lẫn `content_hash` trên toàn bộ 89 chunk** — xác nhận corpus hiện tại đúng là bản gốc
  Minh đã dùng, an toàn để chạy lại `python -m backend.rag.ingest` bất kỳ lúc nào mà không sợ mất
  dữ liệu.
- `pytest backend/tests/` toàn bộ: `49 passed`.

## File thay đổi

- `.gitignore`
- `codebase/backend/knowledge_base/raw/1_map.jpg` (gitignored, không commit)
- `codebase/backend/knowledge_base/raw/2_Handbook_AI_IN_ACTION.txt` (gitignored, không commit)
- `codebase/backend/knowledge_base/raw/3_link_vi_tri.txt` (gitignored, không commit)
- `codebase/backend/knowledge_base/raw/4_gio_mo_cua_library.txt` (gitignored, không commit)
- `codebase/backend/knowledge_base/raw/5_ket_qua_khoa_1.txt` (gitignored, không commit)
- `codebase/backend/knowledge_base/raw/6_loai_phong_va_huong_dan_dat_phong.txt` (gitignored, không commit)

## Khôi phục

Không cần `git revert` — 6 file dữ liệu chưa từng được git track nên không nằm trong lịch sử. Muốn
gỡ bỏ chỉ cần xoá thủ công trong `backend/knowledge_base/raw/`. Riêng thay đổi `.gitignore` thì
revert bình thường theo commit triển khai ở trên nếu cần.
