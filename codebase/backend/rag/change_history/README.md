# RAG Change History

Mỗi lần triển khai RAG thành công phải tạo **một file riêng** trong thư mục này.
Không nối nhiều task vào `README.md`.

## Quy ước tên file

```text
{task}_{YYYY-MM-DD_HH-mm-ss}.md
```

- `task`: slug ngắn, chữ thường, dùng dấu `-`.
- Thời gian: timezone `Asia/Saigon`.
- Không đổi tên file cũ vì tên file là một phần của trace.

Mỗi file phải ghi: thời gian, branch, commit triển khai, commit chứa logic cũ,
logic cũ/mới, file thay đổi, kết quả verify/benchmark, artifact và lệnh
`git revert`/`git cherry-pick`.

## Quy ước commit

```text
minh - {task}
```

Không rewrite commit cũ chỉ để đổi message vì sẽ làm thay đổi hash rollback.
Không tạo commit riêng cho thay đổi nhỏ, format hoặc change-history. Các thay
đổi này được giữ trong working tree và gom vào commit implementation có ý nghĩa
tiếp theo.

## Index

- [Hybrid retrieval](hybrid-retrieval_2026-07-30_15-14-01.md)
- [Resident dense retriever](resident-dense-retriever_2026-07-30_14-57-17.md)
- [Split change history by task](split-change-history-by-task_2026-07-30_14-42-33.md)
- [Local E5 embedding](local-e5-embedding_2026-07-30_14-40-03.md)
- [Phase 1 ingestion baseline](phase-1-ingestion-baseline_2026-07-30_14-12-20.md)
