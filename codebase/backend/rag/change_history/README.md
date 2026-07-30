# RAG Change History

File này là nhật ký append-only cho các lần triển khai RAG thành công. Sau mỗi
lần implement và kiểm thử đạt, thêm một mục mới gồm: thời gian `Asia/Saigon`,
commit, logic cũ/mới, file thay đổi, kết quả kiểm thử và cách rollback.

## Quy ước commit

Mọi commit do role RAG này tạo phải có format:

```text
minh - {task}
```

Không rewrite các commit cũ chỉ để đổi message vì việc đó làm thay đổi hash đã
được dùng trong nhật ký rollback.

## 2026-07-30 14:40:03 +07:00 — Local E5 embedding

- Branch: `minh/rag-design`
- Commit triển khai: `efdbad20bcf14a66cdeb647aa501e83633dc02a1`
- Commit chứa logic cũ: `bbfae41fcedbccdf370518383d50bba3a9a7b6ad`

### Logic cũ

- `build_index()` chưa triển khai và không có document/query embedding.
- Config mặc định dùng remote `text-embedding-3-small`.
- Chưa có vector artifact, provenance check hoặc FAISS index thật.

### Logic mới

- Dùng local `intfloat/multilingual-e5-small`, ONNX CPU, revision pin
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`.
- Document dùng `passage:`, query dùng `query:`; vector float32 384 chiều được
  L2-normalize.
- Model là singleton; cache snapshot được ưu tiên để không kiểm tra mạng khi
  startup. `warm_up()` chuẩn bị model trước khi nhận query.
- Sinh và validate `embeddings.npy`, `dense.faiss`,
  `embedding_manifest.json`; phát hiện chunk/model artifact stale.
- `FAISS_INDEX_DIR` được resolve tuyệt đối để không phụ thuộc working directory.
- Verify: 14 tests passed; artifact `(89, 384)`; warm query 100 runs đạt p50
  5,17 ms, p95 6,00 ms; 5/5 smoke query có top-1 đúng. Cold warm-up 19,2 giây.

### File thuộc thay đổi

- `codebase/backend/config.py`
- `codebase/backend/rag/ARCHITECTURE.md`
- `codebase/backend/rag/embedding.py`
- `codebase/backend/rag/ingest.py`
- `codebase/backend/tests/test_embedding.py`
- `codebase/requirements.txt`

### Khôi phục chính xác

```powershell
git status --short
git revert efdbad20bcf14a66cdeb647aa501e83633dc02a1

# Áp dụng lại implementation lên branch khác
git cherry-pick efdbad20bcf14a66cdeb647aa501e83633dc02a1
```

Vector artifacts không thuộc commit. Sau khi áp dụng lại, cài dependency rồi
chạy `python -m backend.rag.ingest` để tái tạo chính xác.

## 2026-07-30 14:12:20 +07:00 — Phase 1 ingestion baseline

- Branch: `minh/rag-design`
- Commit triển khai: `3dd61a335f8b7e095acbb7a655db9eaf5a91acc9`
- Commit chứa logic cũ: `1c8a31d2822f485bb43f26bfb9ce9a6870ef7cd6`

### Logic cũ

- `ingest.py` chỉ có stub: loader/chunker trả danh sách rỗng.
- `build_index()` luôn ném `NotImplementedError`.
- Chưa có kiến trúc baseline và test ingestion.

### Logic mới

- Chỉ nạp ba nguồn raw đã duyệt: handbook và hai tài liệu thư viện.
- Chunk theo heading, FAQ, giờ mở cửa và từng phòng; giữ ba bước Outlook cùng
  một chunk; giới hạn `1.200` ký tự.
- Deduplicate nội dung file 4/6, ưu tiên file 4 làm nguồn canonical.
- Gắn `source_url`, `content_hash`, `chunk_id`, `heading_path`; ghi
  `chunks.jsonl` và `manifest.json` tái lập được.
- `build_index()` vẫn chưa triển khai vì thuộc phase 2.
- Kết quả: 89 chunks, loại 31 duplicate, 38 chunks có link, max 1.133 ký tự.
- Verify: `pytest backend/tests/test_ingest.py -q` → 5 passed;
  `pytest backend/tests -q` → 6 passed.

### File thuộc thay đổi

- `codebase/backend/rag/ARCHITECTURE.md`
- `codebase/backend/rag/ingest.py`
- `codebase/backend/tests/test_ingest.py`

### Khôi phục chính xác

```powershell
# Xem trạng thái trước khi rollback
git status --short

# Tạo commit đảo ngược an toàn trên lịch sử dùng chung
git revert 3dd61a335f8b7e095acbb7a655db9eaf5a91acc9

# Hoặc áp dụng lại implementation này lên branch khác
git cherry-pick 3dd61a335f8b7e095acbb7a655db9eaf5a91acc9
```

Không dùng `git reset --hard`. Artifact trong `knowledge_base/processed/` được
sinh lại bằng `python -m backend.rag.ingest` và không thuộc commit trên.
