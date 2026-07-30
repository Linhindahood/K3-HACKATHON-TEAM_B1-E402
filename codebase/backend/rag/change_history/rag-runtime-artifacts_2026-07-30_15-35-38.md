# RAG runtime artifacts

- Thời gian: `2026-07-30 15:35:38 +07:00`
- Branch triển khai: `minh/rag-design`
- Branch đã merge: `master_B1_E402`
- Commit triển khai: `d34a68a6e66bc08960c51e630a9ddb984c9cd90d`
- Commit chứa logic cũ: `e7840fb297276a5202cfd8be170235d92892a8ad`
- Kiểu merge: fast-forward, không có conflict

## Logic cũ

- Processed chunks, dense vectors, FAISS và BM25S index chỉ tồn tại local và bị
  `.gitignore` loại khỏi Git.
- Một checkout mới phải có raw data rồi chạy ingestion trước khi retrieval có
  thể load index.

## Logic mới

- Commit 89 processed chunks và manifest.
- Commit embedding matrix 384 chiều, FAISS `IndexFlatIP` và embedding manifest.
- Commit BM25S sparse index và lexical manifest.
- Không thêm bất kỳ file raw mới nào.
- Không commit model weights/cache; E5 revision vẫn được tải từ Hugging Face
  khi máy chưa có cache.
- `master_B1_E402` và `minh/rag-design` cùng trỏ tới commit triển khai.

## Verify

- Audit không tìm thấy credential-like string trong artifacts.
- Diff từ master cũ không có path mới dưới
  `codebase/backend/knowledge_base/raw/`.
- `46 passed` trên `master_B1_E402`.
- Warm-up load được 89 dense chunks và 89 lexical chunks.
- Query không dấu A102 retrieve đúng chunk.
- Grounded generator mock trả đúng một cited source và link whitelist.

## File dữ liệu được thêm

```text
codebase/backend/knowledge_base/processed/chunks.jsonl
codebase/backend/knowledge_base/processed/manifest.json
codebase/backend/rag/vectorstore/embeddings.npy
codebase/backend/rag/vectorstore/dense.faiss
codebase/backend/rag/vectorstore/embedding_manifest.json
codebase/backend/rag/vectorstore/bm25/
```

## Khôi phục riêng commit artifact

```powershell
git status --short
git revert d34a68a6e66bc08960c51e630a9ddb984c9cd90d

# Áp dụng lại trên branch khác
git cherry-pick d34a68a6e66bc08960c51e630a9ddb984c9cd90d
```
