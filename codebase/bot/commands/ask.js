const { client, BACKEND_URL } = require('../client');
const { formatAnswer } = require('../formatting');

/**
 * Nhận câu hỏi từ sinh viên trong Discord, gọi backend /ask, trả lời lại kênh.
 * @param {import('discord.js').Message} message 
 */
async function handleQuestion(message) {
  const question = message.content.replace(/<@!?\d+>/g, '').trim();
  if (!question) {
    return;
  }

  try {
    const response = await fetch(`${BACKEND_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const embed = formatAnswer(data.answer, data.sources);
    await message.channel.send({ embeds: [embed] });
  } catch (error) {
    console.error('Lỗi khi gọi backend FastAPI:', error);
    await message.reply('Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi với backend.');
  }
}

client.on('messageCreate', async (message) => {
  if (message.author.bot) {
    return;
  }
  if (client.user && message.mentions.has(client.user)) {
    await handleQuestion(message);
  }
});

module.exports = {
  handleQuestion,
};
