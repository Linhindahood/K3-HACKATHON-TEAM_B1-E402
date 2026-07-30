# RAG V1 Audit and Upgrade Implementation Plan

> **For agentic workers:** Khi triển khai, dùng `superpowers:subagent-driven-development`
> hoặc `superpowers:executing-plans` theo từng phase và dừng ở review gate sau mỗi
> phase. Tài liệu này chỉ là audit + kế hoạch; chưa cho phép sửa code.

**Goal:** Nâng V0 thành một RAG tiếng Việt an toàn, thân thiện, index toàn bộ raw,
chịu được truy vấn không dấu/lỗi chính tả/khác ngôn ngữ, có link–ảnh–chỉ đường và
handoff rõ ràng mà không làm tăng độ phức tạp không cần thiết.

**Architecture:** Giữ direct Python, multilingual E5 ONNX, FAISS `IndexFlatIP`,
BM25S và provider SDK. Bổ sung source registry, parser theo loại dữ liệu, router
nhẹ, query variants, evidence gate đã calibration và response composer có output
typed. Ảnh chỉ được gửi tới vision model khi route cần ảnh; không thêm vision
vector database ở V1.

**Tech stack:** Python, FastAPI, Sentence Transformers ONNX,
`intfloat/multilingual-e5-small`, FAISS, BM25S, OpenAI Responses API, Discord
client hiện có.

## Global constraints

- Luật ưu tiên số 1: chỉ sửa role RAG. Với bot/API/data boundary, RAG chỉ định
  nghĩa contract và ghi rõ owner cần phối hợp.
- Mọi file trong `knowledge_base/raw/` phải được discovery, parse và có ít nhất
  một logical chunk hoặc ingestion phải fail; không được silently skip.
- Raw không bị sửa bởi role RAG. Placeholder hoặc dữ liệu không đủ metadata làm
  build fail để role data sửa, không được biến thành evidence production.
- Không hiển thị local filename, chunk ID, similarity score hoặc marker `[Sx]`
  cho người dùng.
- Citation, URL, media và handoff target do code kiểm soát; LLM không tự tạo.
- Retrieval/generation không được có tool có side effect.
- Giữ backward compatibility cho `answer`, `sources`, `has_evidence` trong giai
  đoạn chuyển tiếp.
- Chỉ commit khi một phase độc lập đã pass; commit dùng cú pháp
  `minh - {task}`.

---

## 1. Kết luận audit V0

V0 chưa nên được xem là baseline an toàn để mở rộng trực tiếp. Trước khi thêm ảnh
hoặc router, cần khóa các lỗi fail-open và integration regression sau:

### Bằng chứng tại repository hiện tại

- HEAD hiện tại là merge commit `eab5a6d`. `backend/api/routes.py` gọi trực tiếp
  `retriever.retrieve()` và `generator.generate()`, trong khi
  `backend/tests/test_routes.py` vẫn mock `routes.rag_pipeline`. Merge đã làm mất
  coordinator boundary được thêm ở commit `cddf871`.
- `.venv` vẫn trỏ đến Python 3.11 đã bị gỡ nên test suite không thể chạy bằng
  runtime chuẩn của repo.
- Manifest có 89 chunks nhưng chunk artifact chỉ còn canonical chunks từ hai
  nguồn: 51 từ handbook và 38 từ tài liệu thư viện. Tài liệu số 6 bị deduplicate
  hoàn toàn, vì vậy được ghi là `indexed` nhưng không còn chunk provenance độc
  lập.
- 38/89 chunk IDs bị mất `d` do `_slug()` loại ký tự `đ/Đ`, ví dụ
  `huong-dan-at-phong` thay vì `huong-dan-dat-phong`.
- 38/89 chunks có URL; 51 chunks handbook chỉ trả local filename/chunk ID.
- Ba file Markdown raw vẫn là placeholder có câu hướng dẫn điền dữ liệu. Nếu
  index tất cả ngay, những câu hướng dẫn này sẽ trở thành context giả.
- `1_map.jpg` là bản đồ VinUni Open Day 2024 và chứa cả lịch sự kiện. Không có
  metadata tách phần bản đồ lâu dài khỏi nội dung sự kiện có thời hạn.
- `5_ket_qua_khoa_1.txt` chứa số liệu tuyển dụng và thu nhập nhưng chưa có
  `verified_at`, `valid_from`, URL công khai hoặc quy tắc giữ nguyên mẫu số.
- Runtime log hiện có 13 request nhưng cả 13 đều mang intent `general`. Query
  `hello` từng mất 321.111,8 ms vì bị đẩy vào retrieval thay vì fast route.
- `backend/logs/ask_log.jsonl` đang được Git track. Bot logger còn ghi Discord
  user ID, username, channel và guild. Điều này trái với quy tắc không commit
  chatlog/transcript.

## 2. Severity matrix

### P0 — Critical: phải sửa trước mọi feature mới

| ID | Vấn đề | Root cause | Rủi ro | Hướng xử lý |
|---|---|---|---|---|
| P0-01 | `/ask` bypass `pipeline.py` | Merge chọn phiên bản route của role build | Coordinator và test contract lệch nhau; feature router sau này có thể tiếp tục bị bypass | Khôi phục một public entrypoint duy nhất; logging bao quanh pipeline, không copy logic RAG vào route |
| P0-02 | Test runtime không chạy | `.venv` trỏ Python đã bị gỡ | Không thể chứng minh baseline xanh hay phát hiện regression | Rebuild `.venv`, cài dependency trong `.venv`, chạy full suite trước thay đổi |
| P0-03 | Citation fail-open | `cited_passages()` dùng `passages[:1]` khi model không cite | Hệ thống tự gắn nguồn model chưa dùng | Không có valid citation marker thì reject/repair; tuyệt đối không tự gán passage đầu |
| P0-04 | Evidence gate dùng một absolute dense threshold | Chỉ kiểm tra top `dense_score >= 0.82`; bỏ qua BM25, margin, agreement và answer completeness | False accept/false reject; exact room ID có thể bị reject dù BM25 đúng | Calibration trên golden set với nhiều signal; tạm thời fail closed |
| P0-05 | Index-all có thể ingest instruction/placeholder | Không có content preflight hoặc status quality | Evidence giả và indirect prompt injection | Mọi raw phải parse nhưng build production fail khi có placeholder, instruction-like content hoặc metadata bắt buộc bị thiếu |
| P0-06 | Full Q&A và định danh bị log/commit | Logger ghi nguyên văn; log file được track | Lộ dữ liệu học viên và transcript | Role build phải untrack runtime logs; RAG chỉ log decision/latency/hash hoặc dữ liệu đã redaction |
| P0-07 | Không có golden set đủ để calibration | Test chủ yếu mock unit path; không có typo/OOS/image/injection slices | Mọi threshold và nâng cấp đều dựa vào cảm giác | Tạo golden set human-reviewed trước khi tune |
| P0-08 | Retrieved text/image được coi là trusted | Prompt chỉ nhắc không làm theo context nhưng không có ingestion security gate hoặc attack tests | RAG poisoning và multimodal indirect prompt injection | Delimit data, hash/provenance, fail build khi source đổi bất thường, attack set bắt buộc |

`multilingual-e5-small` ghi rõ cosine score thường nằm quanh 0,7–1,0 và thứ tự
tương đối quan trọng hơn giá trị tuyệt đối. Vì vậy `0.82` không thể được coi là
xác suất confidence chung cho mọi domain.

### P1 — High: ảnh hưởng trực tiếp đến độ đúng và trải nghiệm chính

| ID | Vấn đề | Root cause | Giải pháp V1 |
|---|---|---|---|
| P1-01 | Không index toàn bộ raw | `_SOURCES` hard-code ba file; image, URL, khóa 1 và Markdown bị skip | Source discovery + handler registry cho `.txt`, `.md`, `.jpg`; unknown type làm build fail |
| P1-02 | Dedup làm mất provenance | Dedup xóa draft duplicate và chỉ giữ filename canonical | Giữ mọi source chunk record; dedup embedding payload, lưu `canonical_chunk_id` và `source_aliases` |
| P1-03 | Chunk ID mất `đ` | NFKD + ASCII ignore không map `đ → d` | Transliteration rõ ràng trước slug; schema migration và rebuild toàn bộ artifact |
| P1-04 | Long split có thể phá semantic unit | `_split_long()` có nhánh cắt theo ký tự, không sentence boundary/overlap | Split heading → paragraph → sentence; một-sentence overlap khi buộc phải cắt |
| P1-05 | Greeting/identity/help bị retrieval | `_is_searchable()` chỉ cần một ký tự alnum | High-precision router trước embedding; direct response cho non-RAG intents |
| P1-06 | Mọi loại từ chối dùng một câu | Generator chỉ có một fallback thiếu evidence | Decision taxonomy + template riêng cho clarify, OOS, unsupported action, provider failure, handoff |
| P1-07 | Query typo/code-switch yếu | Dense dùng nguyên query; lexical chỉ thêm bản không dấu | Multi-variant retrieval, char n-gram/fuzzy entity candidate, conditional rewrite khi confidence thấp |
| P1-08 | Query khác ngôn ngữ không có policy | Không detect language, BM25 chỉ khớp corpus Việt, prompt luôn yêu cầu tiếng Việt | Giữ dense multilingual; conditional translate/rewrite; trả lời cùng ngôn ngữ cho Việt/Anh |
| P1-09 | Link nguồn không đúng abstraction | `_source_url()` suy đoán bằng heading; handbook không có public URL | Source registry chứa `title`, `public_url`, `allowed_domains`, validity; không suy đoán URL theo text |
| P1-10 | User thấy filename/chunk ID/marker | Generator giữ `[Sx]`; `attach_sources()` dùng local source; bot lại thêm field nguồn | Machine-owned citations, user-facing title/link, strip marker trước response |
| P1-11 | Không có multimodal path | LLM provider chỉ nhận string; E5 không index ảnh | Image asset + reviewed/extracted text chunks; gửi ảnh chỉ ở location route |
| P1-12 | Không thể hướng dẫn đường đi đúng | Chỉ có một ảnh, không origin/destination graph hoặc validity metadata | Route `location`; hỏi origin khi thiếu; landmark graph/region metadata; luôn kèm ảnh |
| P1-13 | Handoff chỉ là câu “liên hệ BTC/TA” | Không có decision hoặc support target typed | `handoff` metadata với reason/target role; bot owner mới map role thành mention |
| P1-14 | Model/index chưa warm khi health OK | `pipeline.warm_up()` không được gọi trong FastAPI lifespan; `/health` chỉ trả OK | Startup warm-up + readiness; một worker; không dùng reload khi demo |
| P1-15 | Thông tin thời gian/xung đột không được quản lý | Chunk không có `verified_at`, validity, authority hoặc supersedes | Metadata thời gian/authority; conflict gate ưu tiên nguồn mới và hỏi lại khi mâu thuẫn |

### P2 — Medium: chất lượng, vận hành và maintainability

| ID | Vấn đề | Root cause | Giải pháp V1 |
|---|---|---|---|
| P2-01 | Câu trả lời khô và kỹ thuật | Prompt chỉ yêu cầu “rõ ràng”; source plumbing lẫn vào answer | `response_policy.py` quản lý tone, độ dài, cách hỏi lại và template |
| P2-02 | Provider failure vẫn trả `has_evidence=True` và toàn bộ sources | Evidence và generation status bị gộp | Thêm `decision=provider_failure`; không trình bày source như câu trả lời hoàn chỉnh |
| P2-03 | Query mơ hồ vẫn có thể trả lời cụ thể | Không có ambiguity/multi-intent gate | Dùng score margin, coverage và clarification question |
| P2-04 | Input không có giới hạn | `AskRequest.question` không có max length/control-char policy | RAG contract đề xuất giới hạn; API owner enforce request size/rate |
| P2-05 | Artifact không chứng minh parser build | Corpus schema v1 thiếu parser version/build ID | Corpus manifest v2 có parser/config/source hashes và build timestamp |
| P2-06 | URL chỉ kiểm tra prefix HTTP | Không canonicalize host, redirect hoặc validity | Exact registry allowlist + canonical URL + link health check offline |
| P2-07 | Health không phản ánh readiness | Không kiểm tra model/index/provider config | `/health` liveness và `/ready` readiness tách biệt |
| P2-08 | Contact có thể lộ email cá nhân | Handbook chứa email ban chỉ đạo và phụ trách | Chỉ handoff tới support role/general channel đã duyệt; không để LLM tự chọn email cá nhân |

### P3 — Low: cải thiện sau khi quality bar đã đạt

- Alt text và crop/region preview cho ảnh.
- Query analytics theo nhóm lỗi nhưng chỉ lưu dữ liệu đã ẩn danh.
- Reranker hoặc embedding model lớn hơn nếu Recall@5 tốt nhưng MRR thấp.
- Hot reload corpus. V1 dùng offline rebuild + process restart để đơn giản và an toàn.

---

## 3. Ba hướng kiến trúc

### A. Patch trực tiếp V0

Sửa slug, thêm vài regex greeting và mở `_SOURCES` cho mọi file. Đây là cách ít
dòng code nhất nhưng vẫn giữ evidence gate, output và provenance dễ fail-open.
Không chọn vì không giải quyết citation, image, temporal metadata và handoff
contract.

### B. Modular V1 giữ nguyên search stack — chọn

Giữ E5/FAISS/BM25S nhưng tách rõ:

```text
raw discovery
  → typed parser + content preflight
  → canonical chunks + provenance aliases + media registry
  → dense/BM25 artifacts

question
  → deterministic router
  → query variants
  → hybrid retrieval
  → calibrated evidence/ambiguity gate
  → grounded text/vision generation
  → citation validator
  → friendly response composer
```

Ưu điểm: sửa đúng boundary, dễ test từng module, không thêm framework/dependency
lớn. Nhược điểm: cần schema migration và phối hợp một lần với role build cho API
output mới.

### C. Chuyển sang framework multimodal/agentic

LlamaIndex/LangChain/Haystack có sẵn router và media abstraction nhưng đổi toàn
bộ document contract, tăng dependency và làm benchmark khó cô lập. Không chọn
cho V1; chỉ xem lại khi corpus hoặc tool workflow tăng lớn.

---

## 4. V1 contracts đề xuất

### 4.1 Source và chunk

```json
{
  "source_id": "handbook-ai-in-action",
  "title": "Handbook AI in Action",
  "local_path": "2_Handbook_AI_IN_ACTION.txt",
  "public_url": "https://official.example/handbook",
  "source_type": "text",
  "authority": 100,
  "verified_at": "2026-07-30",
  "valid_from": "2026-07-30",
  "valid_until": null,
  "content_hash": "sha256"
}
```

```json
{
  "chunk_id": "handbook::quy-dinh::dat-phong",
  "canonical_chunk_id": "handbook::quy-dinh::dat-phong",
  "source_id": "handbook-ai-in-action",
  "source_aliases": ["library-room-guide"],
  "heading_path": ["Quy định", "Đặt phòng"],
  "text": "...",
  "embedding_text": "...",
  "public_anchor": "quy-dinh-dat-phong",
  "media_ids": [],
  "content_hash": "sha256"
}
```

`local_path` chỉ phục vụ audit/benchmark và không đi ra response user.

### 4.2 Router và decision

Intent đóng:

```text
greeting | identity | help | knowledge | location | action | out_of_scope
```

Decision đóng:

```text
direct | answer | clarify | unsupported_action |
out_of_scope | no_evidence | handoff | provider_failure
```

Rule matrix:

| Input | Intent | Decision | Có retrieval/LLM |
|---|---|---|---|
| “xin chào”, “hello” | greeting | direct | Không/không |
| “bạn là ai?” | identity | direct | Không/không |
| “bạn giúp được gì?” | help | direct | Không/không |
| “đặt phòng giúp tôi” | action | unsupported_action | Không/không |
| Câu hỏi rõ trong scope | knowledge/location | answer candidate | Có/có nếu gate pass |
| Câu mơ hồ trong scope | knowledge/location | clarify | Có/không |
| Ngoài scope rõ | out_of_scope | out_of_scope | Không/không |
| Không có evidence | knowledge/location | no_evidence hoặc handoff | Có/không |

Mixed input như “Chào bạn, lịch học ở đâu?” không được route thành greeting; phần
factual vẫn đi retrieval.

### 4.3 Response

```json
{
  "answer": "Câu trả lời thân thiện cho người dùng",
  "sources": ["handbook-ai-in-action"],
  "has_evidence": true,
  "intent": "knowledge",
  "decision": "answer",
  "citations": [
    {
      "source_id": "handbook-ai-in-action",
      "title": "Handbook AI in Action",
      "url": "https://official.example/handbook#quy-dinh-dat-phong"
    }
  ],
  "media": [],
  "handoff": null,
  "follow_up": null
}
```

RAG chỉ trả `target_roles`; Discord owner map role sang mention ID:

```json
{
  "required": true,
  "reason": "in_scope_no_verified_evidence",
  "target_roles": ["btc", "ta"]
}
```

Không cho LLM viết `<@discord-id>` hoặc chọn email cá nhân.

### 4.4 Media và direction

```json
{
  "asset_id": "vinuni-campus-map-2024",
  "source_id": "vinuni-location",
  "type": "image/jpeg",
  "attachment_key": "1_map.jpg",
  "alt_text": "Bản đồ các tòa nhà VinUni",
  "valid_for": ["campus_landmarks"],
  "invalid_for": ["current_event_schedule"],
  "content_hash": "sha256"
}
```

Image route:

1. Retrieve bằng text chunks được trích xuất/kiểm chứng từ ảnh.
2. Chỉ khi intent `location` và media evidence pass mới gửi ảnh gốc cho vision
   model.
3. Nếu thiếu điểm xuất phát, hỏi lại trước khi sinh hướng dẫn.
4. Direction claims phải cite landmark/region chunk; model không tự suy ra lối
   đi ngoài ảnh.
5. Response trả `media`; bot owner gửi attachment cho user.

---

## 5. Implementation phases theo severity

### Phase 0 — Containment, reproducibility và fail-closed baseline

**Files dự kiến:**

- Modify: `backend/api/routes.py`
- Modify: `backend/main.py`
- Modify: `backend/rag/pipeline.py`
- Modify: `backend/rag/evidence_gate.py`
- Modify: `backend/rag/grounding.py`
- Modify: `backend/tests/test_routes.py`
- Modify: `backend/tests/test_generator.py`
- Create: `backend/tests/test_evidence_gate.py`
- Cross-role review: `.gitignore`, backend/bot logger

**Deliverables:**

- [ ] Rebuild `.venv`; full current suite phải collect và pass.
- [ ] `/ask` chỉ gọi `rag_pipeline.answer_question()`.
- [ ] FastAPI lifespan gọi `rag_pipeline.warm_up()`; readiness fail nếu model
  hoặc artifact không load.
- [ ] Không có valid citation thì không attach nguồn.
- [ ] Gate ban đầu fail closed khi dense/lexical không agreement; threshold cuối
  chưa chốt cho tới calibration.
- [ ] Runtime log không còn được Git track; owner logging xác nhận redaction và
  retention.
- [ ] Thêm regression test cho route merge, uncited answer, unknown citation,
  poisoned context và provider failure.

**Verify:**

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Expected: toàn bộ test pass; không có test collection error.

**Review gate:** Chưa thêm feature cho tới khi pipeline boundary và citation
fail-closed được duyệt.

**Commit:** `minh - stabilize rag v0 boundary`

### Phase 1 — Corpus V2: chunk toàn bộ raw, source link và provenance

**Files dự kiến:**

- Create: `backend/rag/source_registry.py`
- Create: `backend/rag/parsers.py`
- Create: `backend/rag/media_registry.py`
- Modify: `backend/rag/ingest.py`
- Modify: `backend/rag/corpus.py`
- Modify: `backend/rag/dense_store.py`
- Modify: `backend/rag/lexical_store.py`
- Modify: `backend/rag/embedding_artifacts.py`
- Modify: `backend/rag/lexical_artifacts.py`
- Modify: `backend/tests/test_ingest.py`
- Create: `backend/tests/test_source_registry.py`
- Create: `backend/tests/test_media_registry.py`

**Deliverables:**

- [ ] Discovery thấy 100% file raw; không còn `_SOURCES` hard-code.
- [ ] `.txt` và `.md` dùng structure parser; `.jpg` tạo asset record và region
  text chunks; URL-only file tạo public-link metadata chunk.
- [ ] Mỗi raw source có ít nhất một logical chunk; zero silent skip.
- [ ] Content preflight làm build fail nếu còn placeholder instructions, source
  thiếu public URL bắt buộc, invalid encoding hoặc image không decode được.
- [ ] `_slug()` map `đ/Đ → d`; stable ID theo `source_id + heading_path`, không
  phụ thuộc local filename.
- [ ] Split theo sentence boundary, không cắt giữa từ; one-sentence overlap chỉ
  khi section vượt token budget.
- [ ] Tất cả source chunks được giữ; embedding dedup dùng canonical chunk nhưng
  bảo toàn aliases/provenance.
- [ ] Source URL lấy từ registry hoặc URL đã parse và allowlist, không dùng
  keyword heuristic.
- [ ] Manifest v2 lưu parser version, source/config hash, media hash, chunk count
  theo source và build ID.
- [ ] Rebuild processed chunks, FAISS và BM25 cùng một build ID.

**Acceptance:**

- Raw coverage = 100%.
- Production build có zero placeholder và zero silent skip.
- 100% chunk IDs có transliteration đúng.
- 100% user-facing source có title; link bắt buộc có public URL hợp lệ.
- Dense/BM25 artifact đều validate cùng corpus build ID.

**Commit:** `minh - build complete rag corpus v2`

### Phase 2 — Router, refusal taxonomy và friendly response

**Files dự kiến:**

- Create: `backend/rag/router.py`
- Create: `backend/rag/response_policy.py`
- Modify: `backend/rag/pipeline.py`
- Modify: `backend/rag/prompt.py`
- Modify: `backend/rag/generator.py`
- Create: `backend/tests/test_router.py`
- Create: `backend/tests/test_response_policy.py`
- Modify: `backend/tests/test_pipeline.py`

**Deliverables:**

- [ ] Router rules chỉ nhận các intent high precision; không dùng hard domain
  route để xóa candidate factual.
- [ ] Greeting, identity, help, unsupported action trả deterministic response,
  không load embedding và không gọi LLM.
- [ ] `no_evidence`, `out_of_scope`, `clarify`, `handoff`,
  `provider_failure` có nội dung khác nhau.
- [ ] Response không còn local filename, chunk ID, score hoặc `[Sx]`.
- [ ] Câu trả lời mặc định ngắn, thân thiện, xưng “mình/bạn”, không lặp lại câu
  hỏi và không đưa giải thích kỹ thuật về retrieval.
- [ ] Câu Việt/Anh trả lời cùng ngôn ngữ; ngôn ngữ khác dùng câu ngắn, không
  giả vờ đã hiểu nếu route confidence thấp.
- [ ] Mixed greeting + factual query vẫn đi RAG.

**Acceptance:**

- Router macro-F1 ≥ 0,95 trên golden set.
- Recall intent `out_of_scope` và `knowledge` ≥ 0,95.
- False reject factual query ≤ 1%.
- Greeting/identity/help p95 ≤ 50 ms và zero model call.

**Commit:** `minh - add rag routing and response policy`

### Phase 3 — Typo, không dấu, abbreviations và cross-language retrieval

**Files dự kiến:**

- Create: `backend/rag/query_variants.py`
- Modify: `backend/rag/query_processing.py`
- Modify: `backend/rag/retriever.py`
- Modify: `backend/rag/fusion.py`
- Modify: `backend/rag/lexical_artifacts.py`
- Modify: `backend/tests/test_query_processing.py`
- Create: `backend/tests/test_query_variants.py`
- Create: `backend/tests/test_retrieval_robustness.py`

**Deliverables:**

- [ ] Luôn giữ `original_query`; mọi rewrite chỉ là retrieval variant.
- [ ] Variants baseline: NFC, whitespace, casefold, diacritic-folded.
- [ ] Benchmark character n-gram BM25 cho typo trước khi thêm spell model.
- [ ] Entity dictionary/fuzzy match chỉ áp dụng cho room IDs, tòa nhà, tên dịch
  vụ và từ khóa corpus; không autocorrect số/email.
- [ ] Dense multilingual chạy trên original query.
- [ ] Chỉ khi initial retrieval uncertainty cao mới gọi conditional
  translate/rewrite; không rewrite mọi request.
- [ ] Fusion deduplicate theo canonical ID và lưu signal theo từng variant.
- [ ] So current linear fusion với RRF trên cùng golden set; không đổi chỉ vì
  benchmark công khai.

**Candidate matrix:**

| ID | Candidate | Chi phí | Quyết định |
|---|---|---|---|
| Q0 | Current native + accentless tokens | Thấp | Control |
| Q1 | Q0 + character 3–5 gram BM25 | Thấp | Candidate ưu tiên |
| Q2 | Q1 + corpus entity fuzzy variants | Thấp | Chỉ giữ nếu false correction thấp |
| Q3 | Q2 + conditional LLM rewrite/translate | Cao hơn | Chỉ cho uncertain cases |

**Acceptance theo từng slice:**

- Recall@3 ≥ 0,90 cho đúng dấu, không dấu, typo nhẹ, English và code-mixed.
- Không slice nào giảm quá 2 điểm phần trăm so với clean Vietnamese.
- Entity corruption rate = 0 trên room IDs, số giờ, email và URL.
- Retrieval warm p95 ≤ 50 ms khi không gọi rewrite.

**Commit:** `minh - improve multilingual query retrieval`

### Phase 4 — Calibrated evidence, citation và public links

**Files dự kiến:**

- Modify: `backend/rag/evidence_gate.py`
- Modify: `backend/rag/grounding.py`
- Modify: `backend/rag/generator.py`
- Modify: `backend/rag/prompt.py`
- Create: `backend/rag/citation_validator.py`
- Modify: `backend/tests/test_generator.py`
- Modify: `backend/tests/test_grounding.py`
- Create: `backend/tests/test_citation_validator.py`

**Deliverables:**

- [ ] Gate dùng top dense, dense margin, BM25, lexical overlap, retriever
  agreement, ambiguity và answer coverage.
- [ ] Threshold chọn từ validation split, ưu tiên giảm false answer.
- [ ] Citation machine-owned; unknown/missing marker fail closed.
- [ ] Mỗi factual claim phải map được tới allowlisted evidence.
- [ ] URL canonical theo source registry; chỉ allowed domain được render.
- [ ] Generator không được thêm nguồn; response composer mới render title/link.
- [ ] Conflict giữa source cùng topic nhưng khác validity dẫn tới clarify hoặc
  handoff, không để LLM tự chọn.

**Acceptance:**

- Citation precision = 100%.
- Unsupported-claim rate ≤ 2%.
- Out-of-scope false accept ≤ 5%.
- Answerability precision ≥ 95%; báo thêm coverage thay vì che số lượng reject.

**Commit:** `minh - calibrate evidence and citations`

### Phase 5 — Multimodal map, image display và directions

**Files dự kiến:**

- Create: `backend/rag/multimodal.py`
- Create: `backend/rag/directions.py`
- Modify: `backend/rag/llm_provider.py`
- Modify: `backend/rag/pipeline.py`
- Modify: `backend/rag/prompt.py`
- Create: `backend/tests/test_multimodal.py`
- Create: `backend/tests/test_directions.py`
- Contract review only: `backend/api/routes.py`, `bot/commands/ask.js`,
  `bot/formatting.js`

**Deliverables:**

- [ ] Image parser tạo reviewed caption/region/landmark chunks cho retrieval.
- [ ] Vision input dùng OpenAI `input_image` chỉ ở `location` route.
- [ ] Server-controlled `asset_id`/attachment key; LLM không tạo path/URL ảnh.
- [ ] Map 2024 chỉ được dùng cho landmarks; lịch Open Day bị đánh dấu expired.
- [ ] Direction query thiếu origin hoặc destination trả clarification.
- [ ] Hướng dẫn đường đi chỉ dùng landmark graph/visible route evidence.
- [ ] Response trả `media` với alt text; bot owner hiển thị attachment.
- [ ] Test ảnh có chữ nhỏ, ảnh xoay, ảnh không liên quan và instruction ẩn.

**Candidate matrix:**

| ID | Candidate | Latency | Accuracy |
|---|---|---:|---|
| M0 | Offline verified caption/regions, không gửi ảnh online | Thấp | Deterministic nhưng thiếu spatial nuance |
| M1 | Gửi ảnh cho vision mọi location query | Cao | Có spatial context nhưng tốn chi phí |
| M2 | Hybrid: text retrieval trước, gửi đúng ảnh khi gate pass | Trung bình | Chọn cho V1 |

**Acceptance:**

- Location Recall@3 ≥ 0,90.
- 100% location answer có đúng source link và media asset khi evidence từ map.
- Zero claim từ phần event schedule đã expired.
- Image route p95 được báo riêng, không trộn vào text-only p95.

**Commit:** `minh - add grounded map and image responses`

### Phase 6 — Structured handoff và cross-role integration

**Files dự kiến:**

- Create: `backend/rag/handoff.py`
- Modify: `backend/rag/response_policy.py`
- Modify: `backend/rag/pipeline.py`
- Create: `backend/tests/test_handoff.py`
- Contract review only: API schema và Discord mention mapping

**Deliverables:**

- [ ] Handoff chỉ bật cho in-scope no-evidence, complaint/sensitive issue hoặc
  explicit request for human.
- [ ] Greeting/OOS thông thường không ping người hỗ trợ.
- [ ] Target dùng role alias được duyệt, không email/Discord ID do LLM sinh.
- [ ] Bot owner quyết định mention thật, cooldown và chống spam.
- [ ] General support channel/email được ưu tiên hơn contact cá nhân.

**Acceptance:**

- Handoff precision ≥ 0,95 trên labeled cases.
- Zero generated personal contact.
- Repeated query không tạo mention storm; phần này do bot owner verify.

**Commit:** `minh - add structured rag handoff`

### Phase 7 — Full benchmark, rollout và rollback

**Files dự kiến:**

- Create: `backend/rag/benchmark/golden_set.jsonl`
- Create: `backend/rag/benchmark/run_retrieval.py`
- Create: `backend/rag/benchmark/run_generation.py`
- Create: `backend/rag/benchmark/README.md`
- Modify: `backend/rag/ARCHITECTURE.md`
- Create: một file `change_history/{task}_{time}.md` cho mỗi phase đã pass

**Golden set tối thiểu 80 cases:**

- 20 clean Vietnamese factual.
- 10 không dấu/NFC-NFD.
- 10 typo/abbreviation.
- 8 English/code-mixed.
- 8 greeting/identity/help/mixed.
- 8 out-of-scope/unsupported action.
- 6 ambiguous/partially answerable/conflicting.
- 6 location/image/direction.
- 4 poisoned text/image.

**Metrics bắt buộc:**

- Router macro-F1 và per-intent recall.
- Recall@1/3/5, MRR@10, nDCG@10 theo query slice.
- Evidence sufficiency precision/recall, false-answer rate và answer coverage.
- Answer correctness, faithfulness và unsupported-claim rate.
- Claim-level citation precision/recall.
- Injection attack success rate.
- p50/p95 cho router, embedding, dense, lexical, fusion, gate, generation,
  image route và end-to-end.
- Startup time, readiness time, RSS và artifact sizes.

**Release gate:**

- Tất cả P0/P1 acceptance pass.
- Full suite pass trong `.venv`.
- Corpus v2, FAISS và BM25 cùng build ID.
- Không có local filename/technical marker trong snapshot responses.
- Không có runtime logs hoặc secret trong Git diff.
- Rollback được bằng commit + artifacts của phase trước theo change history.

**Commit:** `minh - benchmark rag v1 release candidate`

---

## 6. Benchmark decisions, không chọn theo cảm tính

| Trục | Baseline | Candidates |
|---|---|---|
| Chunk | Current structure + char limit | Sentence-boundary child/parent; one-sentence overlap |
| Lexical typo | Native + accentless | Character n-gram; entity fuzzy |
| Query rewrite | None | Conditional translate/rewrite |
| Fusion | Linear alpha 0,7 | Alpha calibration; RRF |
| Gate | Dense 0,82 | Multi-signal calibrated gate |
| Router | None | Rules; rules + E5 prototypes; LLM only uncertain |
| Media | Skipped image | Offline caption; online vision; hybrid |
| Reranker | None | Chỉ thử khi Recall@5 cao nhưng MRR thấp |

Không chạy full Cartesian product. Thứ tự:

1. Chốt corpus/chunk C1.
2. Chốt Q1/Q2 cho typo.
3. Calibration fusion + gate.
4. Router.
5. Citation/generation.
6. Media.
7. Chỉ sau đó mới xét reranker/model lớn.

---

## 7. Những việc cố ý không làm trong V1

- Không đổi sang LangChain/LlamaIndex/Haystack.
- Không graph database.
- Không autonomous agent hoặc tool action.
- Không LLM rewrite trên mọi request.
- Không remote image URL tùy ý.
- Không fine-tune embedding trước khi golden set chứng minh cần.
- Không reranker trước khi biết lỗi nằm ở recall hay ranking.
- Không hot reload artifact trong process.

---

## 8. Cross-role boundaries

### RAG owner được làm

- Ingestion/parser/chunk/index/query/router/gate/generator/grounding.
- Output contract và metadata `citations`, `media`, `handoff`.
- Tests và benchmark RAG.

### Data owner cần xác nhận

- Thay nội dung placeholder hiện có bằng nội dung thật.
- Public URL của handbook và kết quả khóa 1.
- `verified_at`/validity của số liệu, lịch và bản đồ.
- Landmark/region text trích từ ảnh trước khi production.
- General support contact được phép hiển thị.

### Build/bot owner cần triển khai

- API optional fields nhưng giữ backward compatibility.
- Discord attachment/image rendering.
- Mapping `target_roles` → role mention ID, cooldown/chống spam.
- Request size/rate limit.
- Logging redaction/retention và loại runtime log khỏi Git.

RAG owner không tự sửa các phần trên nếu chưa có yêu cầu rõ ràng từ owner tương
ứng.

---

## 9. Research basis

- [Multilingual E5 technical report](https://arxiv.org/abs/2402.05672):
  multilingual retrieval, model size/quality trade-off.
- [Multilingual E5 model card](https://huggingface.co/intfloat/multilingual-e5-small):
  bắt buộc `query:`/`passage:`, 512-token limit, cosine scores không phải
  confidence probability.
- [Vietnamese IR across domains, EACL 2026](https://aclanthology.org/2026.findings-eacl.110/):
  lexical–dense hybrid thường tăng ranking stability; model scale không bảo đảm
  tốt hơn trên mọi domain.
- [ViLexNorm, EACL 2024](https://aclanthology.org/2024.eacl-long.85/):
  biến thể từ vựng tiếng Việt thực tế rất đa dạng; tránh aggressive rewrite.
- [Typo-Robust Dense Retrieval, ACL 2023](https://aclanthology.org/2023.acl-short.95/):
  typo làm giảm dense retrieval và cần typo-aware strategy/evaluation.
- [Code-switching IR, ACL 2026](https://aclanthology.org/2026.findings-acl.636/):
  code-switching vẫn làm giảm chất lượng multilingual retrievers.
- [OpenAI image input quickstart](https://platform.openai.com/docs/quickstart/make-your-first-api-request):
  Responses API nhận `input_text` + `input_image`.
- [OpenAI Images and Vision guide](https://developers.openai.com/api/docs/guides/images-vision):
  image detail và giới hạn đọc chữ/ảnh cần được benchmark.
- [OWASP Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html):
  indirect, RAG-poisoning và multimodal injection.
- [OWASP RAG Security](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html):
  provenance, source validation và retrieval security.
- [Lost in the Middle, TACL 2024](https://arxiv.org/abs/2307.03172):
  thêm nhiều context không đồng nghĩa model dùng evidence tốt hơn.
- [RAGChecker](https://arxiv.org/abs/2408.08067):
  đánh giá riêng retrieval và generation thay vì một score tổng.
- [ALCE citation benchmark, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/):
  citation precision/recall cần đo riêng.
- [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices):
  eval theo task/slice và calibration với human review.

## 10. Thứ tự thực hiện được đề xuất

```text
P0 Phase 0
  → P1 Phase 1 corpus correctness
  → P1 Phase 2 router/response
  → P1 Phase 3 query robustness
  → P0/P1 Phase 4 evidence/citation
  → P1 Phase 5 image/directions
  → P1 Phase 6 handoff
  → Phase 7 release benchmark
```

Không bắt đầu Phase 5 chỉ vì ảnh dễ demo. Nếu Phase 0–4 chưa pass, ảnh làm tăng
thêm một nguồn hallucination và prompt injection thay vì tăng độ đúng.
