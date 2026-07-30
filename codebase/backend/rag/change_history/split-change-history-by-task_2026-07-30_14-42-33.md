# Split change history by task

- Thời gian: `2026-07-30 14:42:33 +07:00`
- Branch: `minh/rag-design`
- Commit triển khai: `dc834c9bd60d885503ffd11215fb05d49e636ea6`
- Commit chứa logic cũ: `4fcf1e55a59c3fde6ff488a9eb1a3ba259a32a69`

## Logic cũ

- Mọi task được nối vào một `README.md`.
- Khi lịch sử dài, khó tìm task theo tên/thời gian và khó mở rộng chi tiết.

## Logic mới

- Mỗi task có một file `{task}_{YYYY-MM-DD_HH-mm-ss}.md`.
- `README.md` chỉ giữ convention và index.
- Hai implementation cũ đã được tách thành file riêng mà không đổi commit hash,
  rollback command hoặc số liệu benchmark.

## File thay đổi

- `codebase/backend/rag/change_history/README.md`
- `codebase/backend/rag/change_history/local-e5-embedding_2026-07-30_14-40-03.md`
- `codebase/backend/rag/change_history/phase-1-ingestion-baseline_2026-07-30_14-12-20.md`

## Verify

- Tên file tuân thủ convention.
- README link được tới từng task.
- Nội dung rollback của hai implementation cũ được giữ lại.

## Khôi phục

```powershell
git status --short
git revert dc834c9bd60d885503ffd11215fb05d49e636ea6

# Áp dụng lại trên branch khác
git cherry-pick dc834c9bd60d885503ffd11215fb05d49e636ea6
```
