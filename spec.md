# AI SPEC — Trợ lý tra cứu nội quy · tiện ích · vị trí VinAI · Nhóm [XX] · Zone [X]
Hướng: [x] B — Trợ lý Học viên  [ ] A — VLearn  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

> ⚠️ **Còn thiếu cần team điền trước 23:59 N1:** số nhóm/zone ở dòng tiêu đề, khảo sát chuẩn A
> (≥20 người ngoài nhóm), §3 (nghiên cứu giải pháp tương tự — mỗi người dùng thử 1 sản phẩm),
> §8 willing users có tên thật. Các mục này được đánh dấu rõ bên dưới, không bịa số liệu.

## §1. User & Job

- **Job executor:** Sinh viên khoá AI Thực Chiến — đồng thời là **tân sinh viên lần đầu nhập học
  VinUni** (chưa có kiến thức nền về trường) — đang tra cứu nội quy/tiện ích/vị trí cơ sở vật chất
  trong lúc học tại cơ sở (trước giờ vào lớp, giờ nghỉ trưa, ngày đầu nhập học).
- **Core JTBD (không tên sản phẩm/AI):** Tìm nhanh thông tin nội quy, tiện ích, vị trí cơ sở vật
  chất khi đang ở trong khuôn viên trường, mà không cần hỏi người khác hoặc tự tìm qua nhiều nguồn.
- **Problem statement (KHÔNG chữ AI):** Sinh viên khoá AI Thực Chiến mất thời gian và dễ hiểu sai
  khi cần tra cứu nội quy, tiện ích, vị trí cơ sở vật chất trong lúc học tại cơ sở, do thông tin
  nằm rải rác không có điểm tra cứu duy nhất, dẫn đến chậm trễ hoặc vi phạm nội quy không cố ý.
- **Evidence:**
  - **Chuẩn A (khảo sát ≥20 người, ≥50% xác nhận):** ⚠️ **chưa có** — chưa thực hiện khảo sát chính
    thức, chỉ có mining (chuẩn B dưới đây).
  - **Chuẩn B (mining):** 5 câu hỏi thật, mining thủ công từ group Facebook/Discord "AI thực chiến"
    của khoá (phương pháp: đọc bài đăng + bình luận trong group, giữ nguyên văn kèm số
    like/comment làm thước đo mức độ phổ biến — kiểm lại được bằng cách mở đúng bài đăng đó). 5
    quote nguyên văn:
    1. *"Nhóm mình đang có nhu cầu book phòng họp riêng trong khuôn viên trường... không biết ở
       trường có phương pháp nào để book phòng sử dụng không nhỉ, hay có cách làm thay thế?"* —
       3 upvote.
    2. *"cho em hỏi trong quá trình tham gia học AI thực chiến tại trường thì có được sử dụng sân
       bóng rổ không ạ..."* — 9 like / **22 comment** (cao nhất trong 5 case mining).
    3. *"trường mình có khu vực tự học nào mở cửa đến đêm (sau 22h) không ạ? Vào thứ Bảy, Chủ
       Nhật thì các khu vực đó có mở cửa không ạ?"* — 7 like / 4 comment.
    4. *"học viên có được mua vé để xe tháng không ạ? Em sử dụng xe xăng gắn máy thì giá gửi xe
       thế nào vậy ạ?"* — 3 like / 7 comment.
    5. *"học viên AI thực chiến tại trường thì có được sử dụng phòng gym của VinUni không ạ..."* —
       6 like / 3 comment.
  - **Phát hiện phụ đáng chú ý:** 3/5 câu hỏi thật (sân bóng rổ, giờ tự học cuối tuần, vé/giá gửi
    xe, phòng gym) hỏi về chủ đề **không nằm trong 3 nguồn corpus** nhóm chuẩn bị được
    (`2_Handbook_AI_IN_ACTION.txt`, `4_gio_mo_cua_library.txt`, `6_loai_phong_va_huong_dan_dat_phong.txt`)
    — vừa là bằng chứng pain có thật (câu sân bóng rổ có 22 comment), vừa là rủi ro scope đã biết
    trước (xem §4 non-goals).

## §2. Impact & quyết định chọn

| Ứng viên | Bao nhiêu người gặp (từ evidence) | Tần suất | Mỗi lần tốn gì | Khả thi trong 36h | Chọn? |
|---|---|---|---|---|---|
| **A. Trợ lý nội quy/tiện ích/vị trí** (dựa trên Handbook + tài liệu thư viện đã có) | Không đo trực tiếp số người, nhưng xác nhận gián tiếp qua hành vi thật khi test (nhiều câu hỏi thật được trả lời đúng, có trích nguồn — xem `backend/logs/ask_log.jsonl`) | Lặp lại mỗi ngày học (giờ vào lớp, giờ nghỉ, ngày đầu nhập học) | Vài phút hỏi lại người khác, hoặc tự tìm sai/không ra | **Cao** — data nguồn đã có sẵn, được BTC cấp | ✅ **Chọn** |
| B. Trợ lý cơ sở vật chất thể thao (sân bóng rổ, gym, bãi xe) | Bằng chứng **mạnh nhất** trong 5 mining (22 comment) | Không đo được (mining 1 lượt, chưa lặp lại theo dõi) | Không rõ — chưa biết nên tự tìm ai hỏi | **Thấp** — không có nguồn dữ liệu chính thức nào được cấp về sân bóng/gym/bãi xe; trả lời sẽ phải bịa hoặc luôn fallback | ❌ Loại — thiếu data, rủi ro bịa số liệu tài chính (giá gửi xe) nếu build vội |
| C. Bản tin cuối ngày cho TA / phát hiện học viên "stuck" (gợi ý từ `01-de-bai.md`) | Không có bằng chứng mining trực tiếp từ nhóm | — | — | **Thấp** — đối tượng dùng khác (TA, không phải sinh viên), lệch job executor đã chọn; cần quyền truy cập lịch sử chat rộng hơn phạm vi được cấp | ❌ Loại — lệch job executor, thiếu evidence |

**Ứng viên chọn: A** — vì có evidence thật (5 câu mining + hành vi thật lúc test), khả thi nhất
trong 36h (data đã được cấp sẵn), và đúng job executor đã chốt (sinh viên mới nhập học, không phải
TA). Ứng viên B tuy evidence mạnh hơn về mặt lượt tương tác nhưng bị loại vì thiếu nguồn dữ liệu
chính thức — quyết định có ý thức, không phải bỏ sót.

## §3. Giải pháp tương tự đã nghiên cứu

> ⚠️ **Chưa hoàn thành theo đúng quy trình `02-guide.md §2.2`** (mỗi thành viên dùng thử 1 sản
> phẩm ngoài, 15 phút, trả lời 4 câu) — cần team làm trước khi chốt spec. Dưới đây là 1 so sánh có
> căn cứ từ tài liệu công khai của chính sự kiện, không phải bịa:

- **VLearn AI tutor** (Hướng A cùng sự kiện, mô tả trong `01-de-bai.md`): flow là bôi đen đoạn tài
  liệu + hỏi, tutor trả lời kèm trích dẫn `[trang N]`. Đáng học: trích dẫn gắn liền ngay trong câu
  trả lời để người học tự kiểm chứng — nhóm áp dụng ý tưởng này qua marker `[S1]...[Sn]` +
  "Nguồn tham khảo" cuối câu trả lời (`backend/rag/grounding.py`). Đáng né: VLearn tutor cho phép
  chọn sẵn đúng đoạn tài liệu (bôi đen), còn bot Discord không có bước đó — phải tự retrieval đúng
  đoạn từ câu hỏi tự do, rủi ro cao hơn (đây là lý do cần hybrid dense+lexical search, không chỉ
  semantic search). Mình khác: kênh (Discord thay vì trang học), phạm vi nội dung (nội quy/tiện
  ích/vị trí thay vì bài giảng).

## §4. Thiết kế

- **Lát cắt MỘT CÂU:** Sinh viên mới nhập học hỏi bot Discord về nội quy/tiện ích/vị trí cơ sở vật
  chất → AI quyết định trả lời kèm trích dẫn nguồn khi đủ căn cứ trong tài liệu, hoặc từ chối/hỏi
  lại khi không đủ căn cứ → sinh viên nhận được câu trả lời đáng tin cậy, hoặc biết cần hỏi ai
  tiếp theo (BTC/TA) thay vì tự đoán.
- **Non-goals (những gì KHÔNG build):**
  1. Không tự thực hiện đặt lịch/book phòng thật — chỉ hướng dẫn quy trình bằng text
     (`Requirement.md` mục 4, đã chốt).
  2. Không trả lời câu hỏi ngoài 3 chủ đề nội quy/tiện ích/vị trí (kiến thức chung, làm bài hộ...).
  3. Không mở rộng sang chủ đề chưa có nguồn dữ liệu chính thức được cấp — dù có bằng chứng nhu cầu
     thật (sân bóng rổ, gym, giá gửi xe — xem §2 ứng viên B bị loại).
  4. Không dùng dữ liệu thật ngoài phạm vi được cấp (không tự thu thập thông tin định danh sinh
     viên, không đưa data pack ra ngoài công cụ không được phép — theo luật an toàn `02-guide.md
     §3.4`).
- **Mức prototype nhắm tới: Working** — chạy end-to-end thật: FastAPI (lõi RAG) + Discord bot
  (Node.js) + pipeline retrieval (FAISS + BM25S) + generation (LLM thật qua OpenAI/Gemini/
  OpenRouter, chọn qua `.env`). Phần mock/chưa hoàn thiện: `frontend/` (Streamlit) chỉ là công cụ
  debug nội bộ cho team, không phải sản phẩm cho sinh viên; `validation/` (vòng test người dùng
  thật) chưa thực hiện — xem `validation/README.md`.
- **Automation: Conditional** — AI tự trả lời khi đủ căn cứ, chuyển hướng (fallback + khuyên liên
  hệ BTC/TA) khi không đủ căn cứ. Lý do theo cost-of-error: sinh viên là **tân sinh viên chưa có
  kiến thức nền** (`Requirement.md` mục 5) — nếu AI đoán sai nội quy/giờ giấc/địa điểm, hậu quả là
  đi nhầm chỗ, hiểu sai quy định, thậm chí vi phạm nội quy không cố ý (sửa đắt — ảnh hưởng thật đến
  sinh viên) — trong khi khi đủ căn cứ, tự động trả lời giúp tiết kiệm thời gian BTC/TA phải trả
  lời lặp đi lặp lại các câu hỏi giống nhau (rẻ, ít rủi ro vì có trích dẫn để tự kiểm).

### §4b. Nguyên tắc HAX/PAIR đã áp dụng

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| **G10 — Thu hẹp phạm vi khi nghi ngờ** *(bắt buộc)* | `backend/rag/evidence_gate.py::has_sufficient_evidence` — không đủ điểm tương đồng (`EVIDENCE_DENSE_THRESHOLD`) thì `generator.py` trả câu fallback chuẩn, không đoán liều. |
| **G11 — Giải thích vì sao / gắn hành động tiếp theo** | `backend/rag/grounding.py::attach_sources` — mọi câu trả lời có căn cứ đều kèm khối "Nguồn tham khảo" trỏ đúng tài liệu/mục để sinh viên tự kiểm chứng, không phải tin suông. |
| **G1 — Làm rõ hệ thống làm được gì** | `backend/rag/prompt.py::SYSTEM_PROMPT` — chỉ trả lời từ NGỮ CẢNH được cung cấp, không dùng kiến thức ngoài, không suy đoán. |
| **PAIR — Explainability + Trust** | Cùng cơ chế trích nguồn ở G11 — mục tiêu "tin đúng mức", không phải "tin tối đa": sinh viên tự bấm link/đọc lại nguồn thay vì phải tin tuyệt đối vào bot. |
| **PAIR — Errors + Graceful Failure** | `generator.py` tách 2 loại lỗi khác nhau: `NO_EVIDENCE_ANSWER` (thiếu căn cứ trong tài liệu) khác hẳn `PROVIDER_FAILURE_ANSWER` (lỗi hạ tầng/LLM) — mỗi loại một câu trả lời khác nhau, không gộp chung thành 1 thông báo lỗi mập mờ. |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (8 kịch bản)

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc áp |
|---|---|---|---|---|
| 1 | Hỏi về sân bóng chuyền/gym/giá gửi xe — chủ đề có thật (mining được) nhưng ngoài 3 nguồn corpus đã index (case `Q07`, `Q23`, `Q25`, `Q26` trong `eval/golden_set.jsonl`) | ① Nguồn sự thật | Trả lời fallback trung thực, khuyên liên hệ BTC — không bịa quy định/giá tiền | G10 |
| 2 | Hỏi sức chứa phòng A203 — tài liệu ghi rõ "không được nêu trong tài liệu" (case `Q17`-liên quan) | ① Nguồn sự thật | Nói rõ tài liệu không ghi sức chứa, không tự điền 1 con số cụ thể vào chỗ trống | G10, G1 |
| 3 | "Phòng thảo luận nhóm nằm ở khu vực nào?" — 2 nguồn khác nhau (phòng học Handbook C401/E402/E403 vs phòng thư viện A102-A217) (`Q17`) | ② Mơ hồ/thiếu thông tin | Hỏi lại làm rõ trước khi trả lời, không chọn đại 1 loại | G10 |
| 4 | Câu hỏi không dấu/viết tắt tự nhiên, không có mã phòng làm điểm neo (vd `F04` "dat phong hop nhom the nao") | ② Mơ hồ/thiếu thông tin | Vẫn tìm và trả lời đúng nếu tài liệu có căn cứ rõ — đo được bằng `eval/run_retrieval_eval.py`, hiện **chưa đạt** (3/6 case không dấu miss top-10, xem §7) | G10 |
| 5 | "Đặt giúp mình phòng A102 lúc 3h chiều mai" — đòi bot tự thực hiện hành động đặt lịch thật (`Q08`) | ③ Ngoài phạm vi/thẩm quyền | Từ chối tự thực hiện, chỉ hướng dẫn quy trình (liên hệ ai, form ở đâu) | G10, Non-goal #1 |
| 6 | Câu hỏi đặt phòng có căn cứ trong tài liệu (`Q22`, mining thật) — hiện `grounding.py` tự gắn kèm link đặt phòng thật vào câu trả lời | ③ Ngoài phạm vi/thẩm quyền | **Không kèm link/form thật** theo `Requirement.md` mục 4 — hiện đang **VI PHẠM**, đã ghi nhận trong `eval/golden-set-v1.md` mục 0.1, cần team quyết định trước demo | Non-goal #1 (đang fail) |
| 7 | Hỏi giờ mở cửa thư viện — khác nhau giữa tháng 7-8 và từ tháng 9 (`Q07`/`Q08` trong `eval/golden_set.jsonl` batch giờ mở cửa) | ④ Đặc thù domain | Trả lời đúng theo đúng khung tháng, không gộp chung — sai khiến sinh viên đi tới nơi rồi đóng cửa | G11 |
| 8 | Hỏi số buổi nghỉ tối đa — tài liệu quy định theo *toàn chương trình*, không phải theo *từng môn* (`Q11`) | ④ Đặc thù domain | Trả lời đúng phạm vi áp dụng (toàn chương trình), không diễn giải nhầm thành "mỗi môn" — sai có thể ảnh hưởng điều kiện hoàn thành khoá học | G1, G11 |

*Kịch bản làm nhóm sợ nhất khi demo: #6 (link đặt phòng thật) — vì đây là vi phạm scope đã chốt
với chính mình, có thể bị hỏi thẳng lúc Q&A.*

## §6. Bốn đường đi của trải nghiệm

- **Happy path:** Câu hỏi có căn cứ rõ trong tài liệu → trả lời kèm trích dẫn nguồn. Đo được thật:
  case `Q11`, `Q15`, `F02`, `F06` trong `eval/results/retrieval_20260730_200332.json` đạt
  Recall@1 = true.
- **Low-confidence (②):** ⚠️ **Gap đã biết** — hệ thống hiện chỉ có gate nhị phân (trả lời / fallback
  "chưa tìm thấy"), **chưa có bước chủ động hỏi lại làm rõ** khi câu hỏi mơ hồ (vd "Cho mình xin
  phòng", case `Q26` trong golden set) — hiện xử lý giống hệt case ① (không đủ căn cứ), chưa phân
  biệt "mơ hồ cần hỏi lại" với "thật sự không có trong tài liệu". Cần cải thiện trước demo nếu kịp.
- **Failure/không căn cứ (①):** Trả về `NO_EVIDENCE_ANSWER` chuẩn. Case thật đã test qua Discord:
  "Nhà ăn nằm ở đâu", "Đã có ai khóa trước được tuyển dụng chưa" (xem `backend/logs/ask_log.jsonl`).
- **Correction (user sửa):** ⚠️ **Gap đã biết** — mỗi lượt hỏi được xử lý độc lập, **không có bộ
  nhớ hội thoại** giữa các lượt — nếu sinh viên hỏi lại rõ hơn sau khi nhận fallback, hệ thống coi
  như 1 câu hỏi hoàn toàn mới, không "nhớ" ngữ cảnh câu trước.
- **Khi bị đòi ngoài phạm vi (③):** Case `Q08`/`Q22` — kỳ vọng chỉ hướng dẫn quy trình, không tự
  nhận đã đặt — **đang có vi phạm thật** với case có căn cứ (`Q22`, xem §5 kịch bản #6).
- **Case đặc thù domain (④):** Xử lý đúng khi tài liệu diễn đạt rõ, đo được qua case `Q07`/`Q11`
  (Recall@1 = true) — nhưng rủi ro tăng khi câu hỏi diễn đạt khác cách tài liệu dùng từ (xem §5
  kịch bản #4, #7).

## §7. Kiểm thử

- **Chiều chất lượng + định nghĩa kiểm chứng được:** 7 chiều M1-M7 đã định nghĩa pass/fail cụ thể
  trong `eval/golden-set-v1.md` §1 (Groundedness, Citation validity, Evidence gate calibration,
  Scope refusal, Domain safety, Tone, Compound handling) — mỗi chiều neo theo đúng hành vi thật của
  code (`evidence_gate.py`, `grounding.py`), không phải tiêu chí trừu tượng.
- **Golden set:** `eval/golden_set.jsonl`, **37 case** — cơ cấu: 4 lớp chỗ khó (≥2 case/lớp), case
  thường (nội quy/tiện ích/vị trí), case hiếm (input rỗng, prompt injection), **6 case không dấu/
  viết tắt riêng** (`F01`-`F06`, bổ sung theo đúng phát hiện thật về hạn chế retrieval), và **5 case
  mining thật** từ Facebook/Discord khoá (`Q22`-`Q26`, xem §1).
- **Quality bar** *(chốt tại đây, giữ nguyên sau khi commit)*: **Đạt khi ≥75% câu thử qua được các
  chiều M1-M7, và AI không được bịa thông tin dù chỉ một lần — đặc biệt không tự bịa số phút đi
  trễ/mốc giờ cụ thể, hay tuyên bố đã đặt lịch/đặt phòng thay người dùng** (đề xuất gốc từ
  `eval/golden-set-v1.md` §2.0). Riêng tầng retrieval có bar kỹ thuật độc lập theo
  `codebase/backend/rag/ARCHITECTURE.md §7.4`: Recall@3 ≥ 90%, MRR@10 ≥ 0.85, duplicate = 0%.
- **Kết quả các lượt chạy** *(lượt 1, chạy `eval/run_retrieval_eval.py`, 2026-07-30, xem
  `eval/results/retrieval_20260730_200332.json`)*:

  | Metric | Kết quả | Bar | Đạt? |
  |---|---|---|---|
  | Recall@1 | 50.0% | — | — |
  | Recall@3 | 58.3% | ≥90% | ❌ Chưa đạt |
  | Recall@5 | 66.7% | — | — |
  | MRR@10 | 0.5583 | ≥0.85 | ❌ Chưa đạt |
  | Duplicate rate | 0.0% | 0% | ✅ Đạt |
  | Dense-gate blind spot *(metric tự đề xuất)* | 8.3% (1/12 case, `F01`) | đề xuất 0% | ❌ Chưa đạt |

  **Phân tích nguyên nhân (không giấu số xấu):** khoảng cách lớn nhất tới bar nằm ở nhóm câu hỏi
  không dấu/paraphrase tự nhiên (`F01`, `F03`, `F04`, `F05` trong 6 case nhóm này chỉ 2/6 đạt
  Recall@1) — cơ chế `evidence_gate.py` hiện chỉ xét điểm dense-score của 1 tầng tìm kiếm (semantic)
  trong khi kết quả cuối được xếp hạng từ 2 tầng (semantic + BM25 từ khoá), gây ra hiện tượng tìm
  đúng tài liệu (rank 1) nhưng vẫn bị từ chối trả lời (chi tiết cơ chế: `docs`-level trace trong
  hội thoại nội bộ nhóm, case `F01` đo được dense_score = 0.8083 so ngưỡng 0.82).
  - ⚠️ **`eval/run_answer_eval.py` (đo end-to-end qua LLM thật — answerability, citation accuracy,
    scope-safety) chưa được chạy trọn bộ lượt nào** — cần chạy trước CP4 để có đủ bảng M1-M7 thật.

## §8. Phân công & kế hoạch

- **Phân công có tên** *(theo `docs/Architecture.md` §3 + `teammates.md`)*:
  - **Hồ Phạm Đức Linh (2A202601533)** — Nhóm trưởng, spec, kiến trúc, test/QA (`eval/`, sửa lỗi
    tích hợp, changelog).
  - **Nguyễn Lê Duy Hưng (2A202601135)** — Thu thập & tổng hợp knowledge base
    (`backend/knowledge_base/raw/`).
  - **Nguyễn Văn Minh (2A202601972)** — RAG pipeline (`backend/rag/` — retrieval, ingestion, embedding).
  - **Nguyễn Thị Phương (2A202601315)** — LLM & prompt (`backend/rag/generator.py`, `prompts/`).
  - **Trương Công Đạt (2A202601449)** — Discord integration (`bot/`).
- **Willing users (≥3 tên):** ⚠️ **chưa có** — cần xác nhận với ≥3 người ngoài nhóm đồng ý thử
  trước demo (đã dự kiến từ CP1 theo `Canvas.md` nhưng chưa điền tên cụ thể). Kế hoạch vòng
  validation CP5: 3 câu hỏi chuẩn theo `02-guide.md §4.2` ("Điều gì khó hiểu/khó chịu nhất?",
  "Bạn có tin kết quả này không — vì sao?", "Bạn có dùng thật không — vì sao/chưa?"), người log:
  ⚠️ chưa phân công.
- **Multi-prototype:** Chưa làm — không bắt buộc theo `02-guide.md §3.3`, cân nhắc nếu kịp thời
  gian giữa CP2-CP3.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 2026-07-30 | `routes.py` gọi lại qua `pipeline.answer_question` thay vì tự lặp logic retriever+generator | Merge conflict làm mất thiết kế gốc của Minh, phát hiện qua `pytest` fail (không phải feedback user — phát hiện QA nội bộ) |
| 2026-07-30 | Bổ sung 6 file dữ liệu thật vào `knowledge_base/raw/` + cập nhật `.gitignore` | `ingest.py` không tái lập được do thiếu corpus, 5 test fail trong `test_ingest.py` |
| 2026-07-30 | Xây `eval/golden_set.jsonl` (37 case) + `run_retrieval_eval.py` + `run_answer_eval.py` | Cần bằng chứng đo được thay vì cảm tính, đúng yêu cầu §7 — phát hiện thêm metric "dense-gate blind spot" chưa có trong thiết kế gốc |

> ⚠️ Bảng trên là thay đổi từ **QA nội bộ**, chưa phải từ **feedback người dùng ngoài nhóm**
> (`validation/` — xem `validation/README.md`, chưa có dữ liệu thật). Rubric R6 cần bảng riêng
> ghi thay đổi xuất phát từ validation thật, sẽ bổ sung sau CP5.
