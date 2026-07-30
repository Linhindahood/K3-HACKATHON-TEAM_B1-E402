# Hybrid retrieval

- Thời gian: `2026-07-30 15:14:01 +07:00`
- Branch: `minh/rag-design`
- Commit triển khai: `500237d79c099504e9e9bd039b40162a5c350482`
- Commit chứa logic cũ: `0a1f89b09bf6eb71583620fbb4fe844f86ffd00d`

## Logic cũ

- Query chỉ đi qua E5 dense embedding và FAISS `IndexFlatIP`.
- Query chỉ được `strip()`, chưa chuẩn hóa Unicode/whitespace.
- Chưa có lexical exact-match cho mã phòng, tên riêng hoặc câu không dấu.
- Manifest dense có lưu prefix nhưng runtime chưa từ chối prefix contract cũ.

## Logic mới

- Dense query tiếp tục dùng E5 `query:`; document dùng `passage:` trong cùng
  không gian vector.
- Query dense chỉ chuẩn hóa Unicode NFC và whitespace, không xóa dấu.
- BM25S index dùng token nguyên dấu và biến thể không dấu trên cùng 89 chunks.
- BM25 artifact có manifest theo ordered `chunk_id`/`content_hash` và phát hiện
  stale corpus/tokenizer.
- Dense top-8 và BM25 top-8 được linear fusion với `alpha=0.7`, deduplicate theo
  `chunk_id`, rồi trả top-k.
- Dense model, FAISS, BM25S và chunk metadata đều resident sau `warm_up()`.
- Runtime xác thực model revision, `query:`/`passage:`, dtype và normalization
  trước khi dùng dense artifact.

## Verify và benchmark

- `31 passed` trong `backend/tests/`.
- `python -m compileall -q backend/rag backend/tests` thành công.
- Ingestion tạo 89 dense chunks và BM25 artifact, reload được ở process mới.
- Dense-only và hybrid cùng đạt top-1 đúng 10/10 smoke queries.
- Query không dấu `phong A102 co bao nhieu cho` trả đúng chunk A102.
- CPU warm hybrid 100 runs: p50 `5,75 ms`, p95 `6,66 ms`, max `12,41 ms`.
- Current runtime: `CPUExecutionProvider`.

## File thay đổi

- `codebase/requirements.txt`
- `codebase/backend/rag/ARCHITECTURE.md`
- `codebase/backend/rag/corpus.py`
- `codebase/backend/rag/dense_store.py`
- `codebase/backend/rag/embedding_artifacts.py`
- `codebase/backend/rag/fusion.py`
- `codebase/backend/rag/ingest.py`
- `codebase/backend/rag/lexical_artifacts.py`
- `codebase/backend/rag/lexical_store.py`
- `codebase/backend/rag/query_processing.py`
- `codebase/backend/rag/retriever.py`
- `codebase/backend/tests/test_dense_store.py`
- `codebase/backend/tests/test_embedding.py`
- `codebase/backend/tests/test_fusion.py`
- `codebase/backend/tests/test_lexical_store.py`
- `codebase/backend/tests/test_query_processing.py`
- `codebase/backend/tests/test_retrieval.py`

## Artifact runtime

Các file sau được sinh bởi ingestion và bị ignore khỏi Git:

```text
codebase/backend/rag/vectorstore/bm25/
codebase/backend/rag/vectorstore/dense.faiss
codebase/backend/rag/vectorstore/embeddings.npy
codebase/backend/rag/vectorstore/embedding_manifest.json
```

Tạo lại bằng:

```powershell
cd codebase
python -m backend.rag.ingest
```

## Khôi phục

```powershell
git status --short
git revert 500237d79c099504e9e9bd039b40162a5c350482

# Áp dụng lại trên branch khác
git cherry-pick 500237d79c099504e9e9bd039b40162a5c350482
```
