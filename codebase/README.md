# codebase/ — Discord Bot hỗ trợ sinh viên VinAI

Kiến trúc & phân công chi tiết: [`../docs/Architecture.md`](../docs/Architecture.md).
Scope sản phẩm: [`../docs/Requirement.md`](../docs/Requirement.md).

## Setup

```bash
cd codebase
python -m venv .venv && source .venv/bin/activate   # hoặc dùng .python-version với pyenv
pip install -r requirements.txt
cp .env.example .env   # rồi điền token/API key thật, KHÔNG commit .env
```

## Chạy từng phần

Backend (FastAPI — bắt buộc chạy trước, cả bot lẫn frontend đều gọi vào đây):

```bash
uvicorn backend.main:app --reload
# http://localhost:8000/health → {"status": "ok"}
```

Discord bot (client gọi backend qua `BACKEND_URL`):

```bash
python -m bot.main
```

Frontend Streamlit (UI demo/debug nội bộ cho team, không phải sản phẩm cuối cho sinh viên):

```bash
streamlit run frontend/app.py
```

Test:

```bash
pytest backend/tests/
```

## Cấu trúc

```
backend/     # FastAPI — lõi RAG (retriever + generator), expose POST /ask
bot/         # Discord client — nhận câu hỏi trong Discord, gọi backend, trả lời embed
frontend/    # Streamlit — UI debug nội bộ, gọi cùng backend
```

Chi tiết từng thư mục, ai sở hữu file nào: xem `../docs/Architecture.md` mục 2-3.
