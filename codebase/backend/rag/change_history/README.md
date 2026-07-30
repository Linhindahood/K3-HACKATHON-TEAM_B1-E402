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

## Index

- [Local E5 embedding](local-e5-embedding_2026-07-30_14-40-03.md)
- [Phase 1 ingestion baseline](phase-1-ingestion-baseline_2026-07-30_14-12-20.md)
