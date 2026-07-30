# Phase 1 ingestion baseline

- Thời gian: `2026-07-30 14:12:20 +07:00`
- Branch: `minh/rag-design`
- Commit triển khai: `3dd61a335f8b7e095acbb7a655db9eaf5a91acc9`
- Commit chứa logic cũ: `1c8a31d2822f485bb43f26bfb9ce9a6870ef7cd6`

## Logic cũ

- `ingest.py` chỉ có stub: loader/chunker trả danh sách rỗng.
- `build_index()` luôn ném `NotImplementedError`.
- Chưa có kiến trúc baseline và test ingestion.

## Logic mới

- Chỉ nạp ba nguồn raw đã duyệt: handbook và hai tài liệu thư viện.
- Chunk theo heading, FAQ, giờ mở cửa và từng phòng; giữ ba bước Outlook cùng
  một chunk; giới hạn 1.200 ký tự.
- Deduplicate file 4/6, ưu tiên file 4 làm nguồn canonical.
- Gắn `source_url`, `content_hash`, `chunk_id`, `heading_path`; ghi
  `chunks.jsonl` và `manifest.json` tái lập được.
- Kết quả: 89 chunks, loại 31 duplicate, 38 chunks có link, max 1.133 ký tự.
- Verify: test ingest 5 passed; toàn bộ backend 6 passed.

## File thay đổi

- `codebase/backend/rag/ARCHITECTURE.md`
- `codebase/backend/rag/ingest.py`
- `codebase/backend/tests/test_ingest.py`

## Khôi phục

```powershell
git status --short
git revert 3dd61a335f8b7e095acbb7a655db9eaf5a91acc9

# Áp dụng lại trên branch khác
git cherry-pick 3dd61a335f8b7e095acbb7a655db9eaf5a91acc9
```

Không dùng `git reset --hard`. Artifact trong `knowledge_base/processed/` được
sinh lại bằng `python -m backend.rag.ingest` và không thuộc commit.
