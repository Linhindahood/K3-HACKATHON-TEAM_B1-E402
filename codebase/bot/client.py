"""[Đạt] Khởi tạo Discord client, intents, event on_ready."""
import os

import discord

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

intents = discord.Intents.default()
intents.message_content = True  # bắt buộc để đọc nội dung tin nhắn khi sinh viên mention bot

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot đã đăng nhập: {client.user} (backend: {BACKEND_URL})")
