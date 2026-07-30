"""[Đạt] Nhận câu hỏi từ sinh viên trong Discord, gọi backend /ask, trả lời lại kênh."""
import httpx

from bot.client import BACKEND_URL, client
from bot.formatting import format_answer


async def handle_question(message) -> None:
    question = message.content.replace(client.user.mention, "").strip()
    if not question:
        return

    async with httpx.AsyncClient(timeout=30) as http_client:
        response = await http_client.post(f"{BACKEND_URL}/ask", json={"question": question})
        response.raise_for_status()
        data = response.json()

    embed = format_answer(data["answer"], data["sources"])
    await message.channel.send(embed=embed)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if client.user in message.mentions:
        await handle_question(message)
