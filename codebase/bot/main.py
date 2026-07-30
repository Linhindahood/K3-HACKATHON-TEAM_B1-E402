"""[Đạt] Entrypoint Discord bot — chạy: python -m bot.main

Bot là client mỏng: nhận câu hỏi trong Discord, gọi backend FastAPI (/ask),
format kết quả thành embed rồi gửi lại kênh.
"""
from bot.commands import ask  # noqa: F401  — đăng ký on_message handler
from bot.client import DISCORD_BOT_TOKEN, client

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        raise SystemExit("Thiếu DISCORD_BOT_TOKEN trong .env — xem .env.example")
    client.run(DISCORD_BOT_TOKEN)
