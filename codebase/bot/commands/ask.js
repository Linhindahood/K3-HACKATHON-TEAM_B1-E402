const { client, BACKEND_URL } = require('../client');
const { formatAnswer } = require('../formatting');
const { logQA } = require('../logger');

/**
 * Nhận câu hỏi từ sinh viên trong Discord, gọi backend /ask, trả lời lại kênh.
 * Ghi log mỗi lượt hỏi-đáp ra file .jsonl.
 * @param {import('discord.js').Message} message 
 */
async function handleQuestion(message) {
  const question = message.content.replace(/<@!?\d+>/g, '').trim();
  if (!question) {
    return;
  }

  const startTime = Date.now();

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
    const responseTimeMs = Date.now() - startTime;

    // Ghi log câu trả lời thành công
    logQA({
      message,
      question,
      answer: data.answer,
      sources: data.sources,
      hasEvidence: data.has_evidence,
      responseTimeMs,
      status: 'success',
    });

    // Format câu trả lời thành Discord Embed kèm ảnh (files) nếu có
    const { embed, files } = formatAnswer(data.answer, data.sources, data.media, data.intent);

    await message.channel.send({
      embeds: [embed],
      files: files.length > 0 ? files : undefined,
    });
  } catch (error) {
    const responseTimeMs = Date.now() - startTime;

    // Ghi log lỗi
    logQA({
      message,
      question,
      responseTimeMs,
      status: 'error',
      error: error.message,
    });

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
