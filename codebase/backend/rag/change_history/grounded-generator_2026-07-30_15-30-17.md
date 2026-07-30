# Grounded generator

- Thời gian: `2026-07-30 15:30:17 +07:00`
- Branch: `minh/rag-design`
- Commit triển khai: `e7840fb297276a5202cfd8be170235d92892a8ad`
- Commit chứa logic cũ: `500237d79c099504e9e9bd039b40162a5c350482`

## Logic cũ

- `generator.py` là stub và luôn trả fallback.
- Chưa gọi LLM provider.
- Chưa có evidence gate chạy trước provider.
- Chưa có citation marker hoặc URL whitelist.
- System prompt runtime chưa được quản lý trong module Python riêng.

## Logic mới

- Bỏ hoàn toàn phase evaluation/golden test suite đã đề xuất trước đó.
- `prompt.py` là nơi duy nhất quản lý system prompt runtime và format context.
- Evidence gate tối giản kiểm tra top dense score trước khi gọi LLM.
- `generator.py` chỉ điều phối gate, prompt, provider và grounded output.
- `llm_provider.py` hỗ trợ resident client cho OpenAI Responses API, OpenRouter
  Chat Completions và Google GenAI.
- Model chỉ được cite marker `[S1]...[Sn]`; code chỉ chấp nhận marker thuộc
  retrieved context.
- `sources` và link cuối câu trả lời chỉ được lấy từ cited passages.
- URL không nằm trong whitelist bị loại khỏi output.
- Lỗi provider có fallback riêng, không bị báo sai thành thiếu evidence.
- API `/ask` vẫn giữ `answer`, `sources`, `has_evidence`.

## Verify

- `46 passed` trong `backend/tests/`.
- `python -m compileall -q backend/rag backend/tests` thành công.
- OpenAI SDK `2.50.0` và Google GenAI SDK `2.15.0` import/config smoke thành công.
- End-to-end mock qua retriever thật:
  - Query không dấu A102 retrieve đúng chunk.
  - Top dense score `0.8707`, gate chấp nhận.
  - Generator trả đúng một cited source.
  - Link room-booking whitelist xuất hiện đúng một lần.
- Không gọi API trả phí trong test.

## File thay đổi

- `codebase/.env.example`
- `codebase/requirements.txt`
- `codebase/backend/config.py`
- `codebase/backend/rag/ARCHITECTURE.md`
- `codebase/backend/rag/evidence_gate.py`
- `codebase/backend/rag/generator.py`
- `codebase/backend/rag/grounding.py`
- `codebase/backend/rag/llm_provider.py`
- `codebase/backend/rag/prompt.py`
- `codebase/backend/tests/test_generator.py`
- `codebase/backend/tests/test_grounding.py`
- `codebase/backend/tests/test_llm_provider.py`
- `codebase/backend/tests/test_prompt.py`

Hai placeholder sau thuộc phần cũ của role khác và không bị chỉnh sửa:

```text
codebase/backend/prompts/system_prompt.md
codebase/backend/prompts/few_shot_examples.md
```

## Cấu hình runtime mới

```text
LLM_PROVIDER
LLM_MODEL
LLM_TIMEOUT_SECONDS
LLM_MAX_OUTPUT_TOKENS
EVIDENCE_DENSE_THRESHOLD
GENERATOR_MAX_PASSAGES
```

## Khôi phục

```powershell
git status --short
git revert e7840fb297276a5202cfd8be170235d92892a8ad

# Áp dụng lại trên branch khác
git cherry-pick e7840fb297276a5202cfd8be170235d92892a8ad
```
