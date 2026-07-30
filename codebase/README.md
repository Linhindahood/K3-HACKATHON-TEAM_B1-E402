# codebase/ — Discord Bot hỗ trợ sinh viên VinAI

Kiến trúc & phân công chi tiết: [`../docs/Architecture.md`](../docs/Architecture.md).
Scope sản phẩm: [`../docs/Requirement.md`](../docs/Requirement.md).

## Setup

**macOS / Linux:**

```bash
cd codebase
python3 -m venv .venv
source .venv/bin/activate   # hoặc dùng .python-version với pyenv
pip install -r requirements.txt
cp .env.example .env   # rồi điền token/API key thật, KHÔNG commit .env
```

**Windows (PowerShell):**

```powershell
cd codebase
python -m venv .venv
.venv\Scripts\Activate.ps1
# Nếu báo lỗi "cannot be loaded because running scripts is disabled":
# chạy 1 lần: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
Copy-Item .env.example .env   # rồi điền token/API key thật, KHÔNG commit .env
```

**Windows (Command Prompt / cmd.exe):**

```bat
cd codebase
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

> Lưu ý Windows: nếu `python` không nhận diện được, thử `py -3.11` thay cho `python`.
> Sau khi activate, dấu nhắc dòng lệnh sẽ hiện `(.venv)` ở đầu — luôn kiểm tra dấu này
> trước khi `pip install` hoặc chạy `uvicorn`/`streamlit`, tránh cài nhầm ra ngoài venv hệ thống.

## Setup bot/ (Node.js)

`bot/` **không** nằm trong venv Python + `requirements.txt` chung nữa — có quy trình cài đặt gói riêng bằng Node.js:

```bash
cd codebase/bot
npm install
cp ../.env.example ../.env   # nếu chưa có — bot/ dùng chung .env với backend/frontend
npm start                     # hoặc: node index.js
```

## Chạy từng phần

Backend (FastAPI — bắt buộc chạy trước, cả bot lẫn frontend đều gọi vào đây):

```bash
uvicorn backend.main:app --reload
# http://localhost:8000/health → {"status": "ok"}
```

Discord bot (Node.js client gọi backend qua `BACKEND_URL`):

```bash
cd codebase/bot
npm start                     # hoặc: node index.js
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
backend/     # FastAPI (Python) — lõi RAG (retriever + generator), expose POST /ask
bot/         # Discord client (Node.js) — nhận câu hỏi trong Discord, gọi backend, trả lời embed
frontend/    # Streamlit (Python) — UI debug nội bộ, gọi cùng backend
```

Chi tiết từng thư mục, ai sở hữu file nào: xem `../docs/Architecture.md` mục 2-3.

