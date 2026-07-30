require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const OpenAI = require('openai');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

client.once('ready', () => {
  console.log(`Bot đã đăng nhập: ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  if (!message.mentions.has(client.user)) return;

  const question = message.content.replace(/<@!?\d+>/g, '').trim();
  if (!question) return message.reply('Bạn muốn hỏi gì?');

  try {
    await message.channel.sendTyping();

    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: question }],
    });

    const text = response.choices[0]?.message?.content ?? '(không có phản hồi)';
    await message.reply(text.slice(0, 2000)); // Discord giới hạn 2000 ký tự
  } catch (err) {
    console.error(err);
    await message.reply('Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu.');
  }
});

client.login(process.env.DISCORD_TOKEN);
