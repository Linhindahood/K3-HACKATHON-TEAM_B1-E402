# RAG Role — Technical Handoff & Change History Document V1

Document này đóng vai trò là tài liệu bàn giao kỹ thuật chính thức từ role **RAG** dành cho các vai trò hợp tác (`data`, `build`, `spec`, `qa`) trong dự án Chatbot Discord hỗ trợ học viên VinAI.

---

## 1. Lịch sử Thay đổi so với Kiến trúc Ban đầu (Change History vs Baseline)

| Thành phần | Kiến trúc Cũ (Baseline Prototype) | Kiến trúc Mới (Phase 1 - Phase 5 Implemented) | Lợi ích & Mục tiêu Kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Intent Router** | Keyword checks đơn sơ trong pipeline text | **Hybrid Fast Path + Few-Shot LLM Intent Router** (`router.py`) với 6 loại Intent (`GREETING`, `IDENTITY`, `HELP`, `UNSUPPORTED_ACTION`, `OUT_OF_SCOPE`, `FACTUAL`) | Phân loại chính xác câu hỏi chào hỏi/ngoài phạm vi/yêu cầu hành động mà không bùng nổ context. |
| **Bảo mật & Injection** | Không có lớp lọc bảo mật | **Security Preflight & XML Context Delimiters** (`security_preflight.py`, `<context_passages>`) | Kháng các cuộc tấn công Prompt Injection/Jailbreak, không để lọt chỉ thị lạ. |
| **Query Processing** | Không có xử lý câu hỏi không dấu | **Accentless Normalization & Query Variant Synthesis** (`query_processing.py`, `query_variants.py`) | Chuẩn hóa câu hỏi không dấu/viết tắt về câu hỏi có dấu sát corpus nhất để tăng recall. |
| **Source Registry** | Không có quản lý metadata nguồn | **Source Metadata Registry** (`source_registry.py`) tự động quét anchor tag và map URL chính thức | Đảm bảo 100% trích dẫn nguồn có link URL chính thức (`https://vinuni.edu.vn/...`). |
| **Retrieval Engine** | Single dense FAISS store | **Hybrid Dense E5 + Lexical BM25 Fusion Store** (`dense_store.py`, `lexical_store.py`, `fusion.py`) | Kết hợp ngữ nghĩa sâu (Dense) và từ khóa chính xác (Lexical BM25) để tìm đúng phòng/tiện ích. |
| **Evidence Gating** | Threshold đơn giản | **Multi-Signal Calibrated Evidence Gate V1** (`evidence_gate.py`) | Đánh giá 4 tín hiệu đồng thuận (Top Score, Margin, BM25 Score, Count) để quyết định Fail-Closed. |
| **Citation Verification** | LLM tự ghi marker không kiểm soát | **Machine-Owned Citation Validator V1** (`citation_validator.py`) | Tự động xóa nhãn mồ côi `[S1]`, `[S2]` và ngắt luồng nếu LLM bịa đặt nguồn. |
| **Multimodal Directions** | Không hỗ trợ chỉ đường / bản đồ | **Dedicated Vision LLM Branch V1** (`directions.py`, `multimodal.py`, `media_registry.py`) | Nạp ảnh `1_map.png` sang Vision API, mặc định Cổng chính, và tự động gắn `media` assets. |

---

## 2. API Contract Stability (RAG Boundary)

Interface duy nhất của module RAG đối với API backend (`backend/api/routes.py`) là hàm:
`answer_question(question: str) -> dict`

### Contract Schema Output:
```json
{
  "answer": "Phòng A102 có sức chứa 8 chỗ. [S1]\n\nNguồn tham khảo:\n- [4_gio_mo_cua_library.txt#danh-sach-phong-va-trang-thiet-bi-phong-a102](https://library.vinuni.edu.vn/about-us/hours-and-access/)",
  "sources": [
    "4_gio_mo_cua_library.txt#danh-sach-phong-va-trang-thiet-bi-phong-a102"
  ],
  "has_evidence": true,
  "intent": "factual",
  "media": [
    {
      "asset_id": "vinuni-campus-map-2024",
      "title": "Bản đồ khuôn viên VinUniversity",
      "url": "https://vinuni.edu.vn/campus-map/",
      "local_path": "1_map.png",
      "alt_text": "Bản đồ các tòa nhà và phòng học VinUniversity"
    }
  ]
}
```

---

## 3. Hướng dẫn Kiểm thử & Vận hành cho các Role

### Cho Role QA:
- **Chạy Automated Unit Test Suite (83 Test Cases)**:
  ```powershell
  cd codebase
  .\.venv\Scripts\python.exe -m pytest backend/tests/ -v
  ```
- **Chạy E2E Verification với Live OpenAI API**:
  ```powershell
  .\.venv\Scripts\python.exe backend/rag/test_live_llm.py
  ```

### Cho Role Data:
- Khi thêm/sửa file trong `codebase/backend/knowledge_base/raw/`, hãy chạy lại script Ingest để build lại Index:
  ```powershell
  python -m backend.rag.ingest
  ```
- Đảm bảo các file tài liệu mới có cấu trúc heading dạng Markdown (dùng `#`, `##`) để `source_registry.py` tự động nhận diện anchor tag.

### Cho Role Build / Discord Bot / Frontend:
- API response `/ask` luôn trả về đúng các key `answer`, `sources`, `has_evidence`, `intent`, `media`.
- Nếu `media` có phần tử, Frontend / Discord Bot có thể lấy `media[0]['url']` hoặc `media[0]['local_path']` để hiển thị ảnh bản đồ đính kèm.

---

## 4. Bảo mật & Quy tắc RAG
1. **Bảo mật Credentials**: Tuyệt đối không commit file `.env`, `OPENAI_API_KEY`, hoặc token lên Git.
2. **Quy tắc An toàn Fail-Closed**: Khi không tìm thấy chứng cứ chắc chắn trong dữ liệu, hệ thống tự động trả về phản hồi fallback thân thiện, tuyệt đối không suy đoán hay bịa đặt.
