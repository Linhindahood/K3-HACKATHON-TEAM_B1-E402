# Resident dense retriever

- Thời gian: `2026-07-30 14:57:17 +07:00`
- Branch: `minh/rag-design`
- Commit triển khai: `0a1f89b09bf6eb71583620fbb4fe844f86ffd00d`
- Commit chứa logic cũ: `e220a0398e8bc1bd5644634befbf630ae016081f`

## Logic cũ

- `retriever.py` là stub và luôn trả danh sách rỗng.
- Embedding model lifecycle và artifact/FAISS logic nằm chung một file.
- ONNX provider bị cố định ở CPU.
- Chưa có runtime giữ model, index và chunk metadata sống sau warm-up.

## Logic mới

- `retriever.py` chỉ validate/fast-reject, embed query và điều phối DenseStore.
- `embedding_model.py` quản lý E5 singleton, cache model và tự chọn
  `CUDAExecutionProvider` trước `CPUExecutionProvider`.
- `embedding_artifacts.py` build/load/validate vector, manifest và FAISS.
- `dense_store.py` giữ strong reference tới FAISS và ordered chunks bằng
  process cache.
- `retriever.warm_up()` load cả store và model; không reload theo request.
- Passage giữ `text`, stable `source`, `score`, `chunk_id`, `source_url`.

## Verify và benchmark

- 22 backend tests passed.
- Artifact: 89 chunks, vector 384 chiều, `IndexFlatIP`.
- Current runtime: `CPUExecutionProvider`; máy test không có CUDA ONNX provider.
- Cold warm-up: 11,85 giây.
- Warm retrieval 100 runs: p50 6,25 ms; p95 7,99 ms.
- 5/5 smoke query có top-1 đúng.
- Store/model giữ cùng object identity sau warm-up.

## File thay đổi

- `codebase/backend/config.py`
- `codebase/backend/rag/ARCHITECTURE.md`
- `codebase/backend/rag/dense_store.py`
- `codebase/backend/rag/embedding.py`
- `codebase/backend/rag/embedding_artifacts.py`
- `codebase/backend/rag/embedding_model.py`
- `codebase/backend/rag/ingest.py`
- `codebase/backend/rag/retriever.py`
- `codebase/backend/tests/test_dense_store.py`
- `codebase/backend/tests/test_embedding.py`
- `codebase/backend/tests/test_retrieval.py`
- `codebase/requirements.txt`

## Khôi phục

```powershell
git status --short
git revert 0a1f89b09bf6eb71583620fbb4fe844f86ffd00d

# Áp dụng lại trên branch khác
git cherry-pick 0a1f89b09bf6eb71583620fbb4fe844f86ffd00d
```
