"""[Đạt] Format câu trả lời backend thành Discord embed."""
import discord


def format_answer(answer: str, sources: list[str]) -> discord.Embed:
    embed = discord.Embed(description=answer, color=discord.Color.blue())
    if sources:
        embed.add_field(name="Nguồn", value="\n".join(f"- {s}" for s in sources), inline=False)
    return embed
