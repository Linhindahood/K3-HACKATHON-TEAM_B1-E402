# eval/ — Golden set & bảng kết quả (rubric R4)

> Vai trò: QA/tester kiểm soát chất lượng câu trả lời. Chấm trên `04-rubric.md` R4 (`spec.md §7` +
> thư mục này).

## File trong thư mục này

- **`golden-set-v1.md`** — bộ 31 case gốc (đọc cho người): định nghĩa 7 metric M1-M7 cần chấm tay
  (groundedness, citation validity, evidence gate, scope refusal, domain safety, tone, compound
  question), quality bar theo từng metric, và 2 vấn đề mở cần team chốt (mục 0.1, 0.2 trong file).
- **`golden_set.jsonl`** — **bổ sung mới**: transcribe lại 31 case trên + thêm 6 case (`F01-F06`)
  sang schema máy đọc được `{id, question, answerable, expected_chunk_ids, category, notes,
  special_check}`, có `expected_chunk_ids` xác minh thật từ `codebase/backend/knowledge_base/processed/chunks.jsonl`
  (89 chunk hiện có) để 2 script dưới đây chấm tự động được. Không sửa `golden-set-v1.md`.
- **`run_retrieval_eval.py`** — chấm **bộ 1: retrieval**. Chạy local, miễn phí, không gọi LLM.
- **`run_answer_eval.py`** — chấm **bộ 2: câu trả lời cuối** (end-to-end qua `backend.rag.pipeline`,
  gọi LLM thật theo `LLM_PROVIDER` trong `.env`).
- **`results/`** — output mỗi lượt chạy (`retrieval_<timestamp>.json`, `answer_<timestamp>.json`).
  Đây là artifact rubric R4 yêu cầu ("bảng kết quả chạy trọn bộ ≥1 lượt") — **commit vào repo**,
  không gitignore.

## Chạy

Cần `codebase/.env` đã điền key thật (xem `codebase/README.md`) và đã chạy
`python -m backend.rag.ingest` ít nhất 1 lần (build FAISS + BM25S index).

```bash
# Bộ 1 — retrieval only, miễn phí, chạy trước để debug retriever độc lập với LLM
python eval/run_retrieval_eval.py

# Bộ 2 — end-to-end thật, tốn API quota nhỏ (37 case, model rẻ)
python eval/run_answer_eval.py
```

Chạy được từ bất kỳ thư mục nào — 2 script tự resolve path tới `codebase/` và `.env`.

## Bộ 1 — Retrieval (`run_retrieval_eval.py`)

| Metric | Định nghĩa | Quality bar (ARCHITECTURE.md §7.4) |
|---|---|---|
| Recall@1/3/5 | Đoạn đúng (`expected_chunk_ids`) có nằm trong top-k sau fusion không | Recall@3 ≥ 90% |
| MRR@10 | 1/rank của đoạn đúng đầu tiên trong top-10 | ≥ 0.85 |
| Duplicate rate | Trùng `chunk_id` trong top-k cuối | 0% |
| **Dense-gate blind spot rate** *(metric mới)* | % case retrieval tìm đúng top-1 **nhưng** `evidence_gate.has_sufficient_evidence` vẫn từ chối vì gate chỉ nhìn `dense_score` của passage top-1, không nhìn điểm đã fusion (dense+BM25) | Đề xuất 0% — xem giải thích ở mục "Câu hỏi không dấu" bên dưới |

## Bộ 2 — Câu trả lời cuối (`run_answer_eval.py`)

| Metric | Định nghĩa | Quality bar |
|---|---|---|
| Answerability precision/recall | `has_evidence` trả về có khớp nhãn `answerable` trong golden set không | — |
| False-accept rate | % case `answerable=false` mà bot vẫn trả lời (`has_evidence=true`) | ≤ 5% |
| Citation source accuracy | `sources` trả về có khớp `expected_chunk_ids` không — đây là cách **tự động hoá "đúng trọng tâm + đúng nguồn"** theo lựa chọn đã chốt | 100% |
| Scope-safety | Case có `special_check` (đặt lịch): answer không được tự nhận "đã đặt"/"đã book" và (với `no_self_action_no_real_url`) không được chứa URL thật | 100% |
| Latency p50/p95 | Đo end-to-end `/ask` | p95 ≤ 3s |

**Giới hạn đã biết của citation-accuracy-làm-proxy-cho-on-topic:** cách này bắt được lỗi "trích sai
nguồn" nhưng **không** bắt được lỗi "trích đúng nguồn nhưng trả lời lạc đề/diễn giải sai nội dung
đoạn đó". Nếu cần bắt loại lỗi này, quay lại M1 (groundedness, chấm tay) trong `golden-set-v1.md`,
hoặc bổ sung LLM-judge sau (đã cân nhắc, tạm không chọn theo yêu cầu tối ưu tốc độ/khách quan cho
36h).

## Câu hỏi không dấu vẫn không trả lời được — có thật không?

**Có**, và cơ chế cụ thể là: `backend/rag/evidence_gate.py::has_sufficient_evidence` chỉ đọc
`dense_score` của passage top-1 (điểm cosine similarity thô từ FAISS, **trước** khi fusion với
BM25), so với `EVIDENCE_DENSE_THRESHOLD=0.82`. Trong khi đó `fusion.py` xếp hạng top-1 dựa trên
điểm đã trộn `0.7 * dense + 0.3 * lexical` — nghĩa là một câu hỏi không dấu có thể được BM25 (vốn
đã lập chỉ mục token không dấu, xem `query_processing.lexical_tokens`) khớp đúng và đẩy lên hạng 1
sau fusion, nhưng nếu `dense_score` riêng của passage đó (so giữa embedding câu hỏi không dấu và
embedding tài liệu có dấu) thấp hơn 0.82, gate vẫn từ chối — bot trả lời "chưa tìm thấy thông tin"
dù retrieval đã tìm đúng.

Case `F02` trong golden set (`phong A102 co bao nhieu cho`) là chính câu Minh đã smoke-test thủ
công (`rag/change_history/grounded-generator_...md`): dense_score đo được `0.8707`, chỉ cao hơn
ngưỡng `+0.0507` — biên độ rất mỏng. Case `F04` (`dat phong hop nhom the nao` — câu tự nhiên hơn,
không có mã phòng làm token neo) là ứng viên nhiều khả năng lộ đúng blind spot này. Chạy
`run_retrieval_eval.py` để có số liệu thật thay vì suy đoán — xem mục "Dense-gate blind spot rate"
ở bảng trên.

## 2 metric bổ sung được đề xuất (ngoài danh sách đã có trong ARCHITECTURE.md §7.2)

1. **Dense-gate blind spot rate** (đã triển khai ở trên) — vá lỗ hổng: các metric retrieval hiện
   có (Recall/MRR) đo khả năng TÌM đúng đoạn, nhưng không đo khả năng gate có "tin" kết quả tìm
   được hay không — 2 thứ có thể lệch nhau như đã giải thích ở trên.
2. **Scope-safety compliance rate** (đã triển khai trong bộ 2) — vá lỗ hổng tương tự cho tầng sinh
   câu trả lời: các metric M1-M7 trong `golden-set-v1.md` đo đúng/sai nội dung, nhưng cần thêm 1
   lớp kiểm tra tự động lặp lại được cho đúng 1 quy tắc cứng và rủi ro cao nhất của dự án
   (`Requirement.md` mục 4: không tự đặt lịch thật, không link/form thật) — quy tắc này càng cần
   tự động hoá vì `golden-set-v1.md` mục 0.1 đã chỉ ra `grounding.py` hiện **vi phạm** quy tắc này
   (tự gắn `ROOM_BOOKING_URL` thật) — cần con số lặp lại được để theo dõi khi team sửa.
