# GEMINI.md — VinAI Discord Bot / RAG Role

## Mục đích của file này

Đây là hướng dẫn dành cho coding agent làm việc trong repository prototype chatbot Discord hỗ trợ học viên khoá VinAI thực chiến.

**Luật ưu tiên số 1:** người phụ trách trong ngữ cảnh này chỉ làm role **RAG**. Không chỉnh sửa, mở rộng hoặc refactor các role khác (`data`, `build`, `spec`, `qa`) nếu người dùng không yêu cầu rõ ràng.


## 1. Think Before Coding
* **State assumptions explicitly:** If any instruction or requirement is ambiguous, do not pick an interpretation silently. Stop and ask for clarification.
* **Surface tradeoffs:** Present multiple potential interpretations or implementations before jumping into code.
* **Push back when warranted:** If a much simpler approach exists that fulfills the core request, point it out instead of overbuilding.
* **Stop when confused:** Clearly name what is unclear and pause execution.

## 2. Simplicity First
* **Write minimum code:** Deliver the absolute minimum amount of code required to solve the specific problem. 
* **Zero speculative engineering:** Do not add features, configuration, or flexibility that nobody explicitly asked for.
* **No premature abstractions:** Avoid building design patterns, wrappers, or classes for single-use code.
* **Optimize for readability:** If a 200-line solution can be safely written in 50 lines, rewrite it.

## 3. Surgical Changes
* **Touch only what you must:** Edit only the specific lines and files required by the task. 
* **Do not "improve" adjacent code:** Avoid rewriting neighboring code, altering unrelated formatting, or adding type hints to other modules.
* **Match the existing style:** Strictly adhere to the codebase's current style, naming conventions, and architecture—even if you prefer a different design.
* **Do not clean up unrelated dead code:** If you notice dead code nearby, mention it in text but do not delete it unless instructed.

## 4. Goal-Driven Execution
* **Define success criteria upfront:** Before writing a single line of code, transform vague, imperative tasks into verifiable targets.
* **Transform vague prompts into tests:** 
  * Instead of "Add validation", change to: "Write tests for invalid inputs, then make them pass."
  * Instead of "Fix the bug", change to: "Write a failing test that reproduces the bug, then make it pass."
* **State a multi-step plan:** For complex tasks, explicitly map out your sequence (e.g., Step 1 -> Verify; Step 2 -> Verify) before execution.
* **Loop until verified:** Run tests or verification tools independently to confirm the success criteria are 100% met before declaring the task complete.

## 5. Code Structure Principles
* **File-per-class:** Each class should reside in its own file, following PascalCase naming conventions.
* **Dependency Injection:** Classes must rely on dependencies being passed through constructors (constructor injection). Avoid static dependencies or hardcoded imports from sibling modules.
* **Circular Dependency Prevention:** When modules A and B require each other, introduce a third module C to break the cycle, or refactor the shared logic into C.


## Bài toán sản phẩm

Chatbot trả lời câu hỏi của học viên trong Discord về ba nhóm thông tin:

- Nội quy khoá học/trường.
- Tiện ích sinh viên.
- Vị trí cơ sở vật chất.

Bot phải trả lời dựa trên tài liệu chính thức được đưa vào knowledge base, có trích dẫn nguồn. Khi không tìm thấy căn cứ đủ chắc chắn, bot phải nói rõ là chưa có thông tin chắc chắn và hướng người dùng hỏi rõ hơn hoặc liên hệ BTC/TA. Bot không được bịa thông tin.

Các câu hỏi về đặt lịch hoặc book phòng chỉ được trả lời bằng hướng dẫn quy trình dạng text; prototype không được tự thao tác đặt lịch và không được giả vờ đã đặt lịch thành công.

## Kiến trúc hiện tại

```text
Discord bot / Streamlit debug UI
              │ HTTP POST /ask
              ▼
FastAPI backend
              │
              ├── RAG retriever: query embedding → top-k passages
              └── RAG generator: evidence threshold → prompt → LLM answer
```

Các boundary cần giữ nguyên:

- `codebase/bot/`: Discord client mỏng; không chứa logic RAG.
- `codebase/frontend/`: Streamlit debug UI; gọi backend qua HTTP.
- `codebase/backend/api/routes.py`: API contract `/ask`; chỉ thay đổi khi thật sự cần cho RAG và phải giữ response tương thích.
- `codebase/backend/rag/`: vùng sở hữu chính của role RAG.

## Phạm vi được phép thay đổi

Chỉ thay đổi các phần cần thiết cho pipeline RAG:

- `codebase/backend/rag/ingest.py`: load tài liệu, chunk, embedding và build FAISS index.
- `codebase/backend/rag/retriever.py`: load index, embed query, similarity search, top-k và metadata nguồn.
- `codebase/backend/rag/generator.py`: evidence gating, prompt assembly, gọi LLM, fallback và source handling.
- `codebase/backend/prompts/`: system prompt/few-shot nếu trực tiếp phục vụ chất lượng RAG.
- `codebase/backend/config.py`: chỉ thêm/sửa cấu hình trực tiếp cần cho embedding, vector store, threshold hoặc provider.
- `codebase/backend/tests/`: test liên quan ingest, retrieval, evidence gating và generator.

Không tự ý sửa:

- `codebase/bot/` và `codebase/frontend/`.
- Nội dung knowledge base/raw thuộc role data.
- Spec, rubric, validation, reflection hoặc tài liệu phân công thuộc role spec/qa.
- API/UI/Discord behavior không liên quan trực tiếp đến RAG.

Nếu phát hiện thiếu dữ liệu nguồn, thiếu API contract hoặc cần thay đổi role khác, dừng ở mức ghi nhận blocker và báo người phụ trách tương ứng; không tự điền dữ liệu giả vào phần của họ.

## RAG contract

Retriever phải trả về danh sách theo format:

```python
[
    {
        "text": "...",
        "source": "noi_quy.md#trang-phuc",
        "score": 0.82,
    }
]
```

Generator nhận `question` và `passages`, trả về:

```python
{
    "answer": "...",
    "sources": ["noi_quy.md#trang-phuc"],
    "has_evidence": True,
}
```

Quy tắc xử lý:

1. Không có passage hoặc điểm cao nhất thấp hơn `SIMILARITY_THRESHOLD` → fallback, `sources=[]`, `has_evidence=False`.
2. Có evidence → chỉ đưa các passage phù hợp vào prompt và yêu cầu model trả lời từ context.
3. Câu trả lời có căn cứ phải nêu nguồn tương ứng.
4. Không biến similarity score thành sự thật tuyệt đối; threshold phải được kiểm thử trên golden set.
5. Không log API key hoặc nguyên văn data pack nhạy cảm.

## Dữ liệu và bảo mật

- Knowledge base runtime: `codebase/backend/knowledge_base/raw/`.
- Processed chunks: `codebase/backend/knowledge_base/processed/`.
- FAISS index: `codebase/backend/rag/vectorstore/`.
- Dữ liệu nghiên cứu trong `data/vlearn-pack/` chỉ dùng trong phạm vi hackathon.
- Không commit nguyên chatlog/transcript vào repo sản phẩm, không upload toàn bộ data ra công cụ ngoài, không cố suy ngược danh tính từ ID ẩn danh.
- Không commit `.env`, API key, token hoặc credentials.

## Lệnh phát triển và kiểm thử

Chạy từ thư mục `codebase/`:

```powershell
pip install -r requirements.txt
pytest backend/tests/
uvicorn backend.main:app --reload
python -m backend.rag.ingest
```

Khi kiểm thử end-to-end, kiểm tra tối thiểu:

- Câu hỏi có tài liệu phù hợp trả được answer và source.
- Câu hỏi ngoài knowledge base kích hoạt fallback, không bịa.
- Similarity threshold hoạt động đúng.
- Metadata source không bị mất từ ingest đến API response.
- Index được tạo và load lại được ở process khác.

## Quy tắc sửa code

- Đọc file liên quan và test hiện có trước khi sửa.
- Ưu tiên thay đổi nhỏ, một mục tiêu mỗi lần.
- Giữ nguyên public contract và style hiện tại nếu không có lý do kỹ thuật rõ ràng.
- Không thêm abstraction/configuration chưa cần thiết.
- Mọi bug fix quan trọng phải có test tái hiện hoặc test hồi quy.
- Sau sửa đổi, chạy test RAG; nếu không chạy được do dependency/API key, ghi rõ blocker thay vì giả vờ đã verify.
- Không chỉnh sửa role khác để “tiện tay” dọn code.

## Tiêu chí hoàn thành cho role RAG

Một thay đổi RAG chỉ được xem là hoàn thành khi:

- Pipeline ingest/retrieve/generate có boundary rõ ràng.
- Có test cho cả trường hợp có evidence và không có evidence.
- Kết quả trả về giữ đúng `answer`, `sources`, `has_evidence`.
- Câu trả lời không có căn cứ không được trình bày như sự thật.
- Không làm thay đổi phạm vi hoặc trách nhiệm của role khác.
- `git diff` chỉ chứa các file liên quan trực tiếp đến RAG.

## Tài liệu tham chiếu

- `README.md`: yêu cầu hackathon và quy định dữ liệu.
- `CLAUDE.md`: context dự án hiện tại.
- `codebase/README.md`: setup và cách chạy prototype.
- `codebase/backend/prompts/system_prompt.md`: nguyên tắc trả lời của bot.
- `data/vlearn-pack/README.md`: phạm vi sử dụng và bảo mật data pack.
- `data/vlearn-pack/chatlog/DATA_DICTIONARY.md`: schema chatlog nếu cần xây golden set/evidence.
