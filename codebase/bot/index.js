/**
 * Entrypoint Discord bot — chạy: node index.js hoặc npm start
 * 
 * Bot là client mỏng: nhận câu hỏi trong Discord, gọi backend FastAPI (/ask),
 * format kết quả thành embed rồi gửi lại kênh.
 */
const { client, DISCORD_BOT_TOKEN } = require('./client');
require('./commands/ask');

if (!DISCORD_BOT_TOKEN) {
  console.error('Thiếu DISCORD_BOT_TOKEN trong .env — xem .env.example');
  process.exit(1);
}

client.login(DISCORD_BOT_TOKEN).catch((err) => {
  console.error('Không thể đăng nhập Discord bot:', err);
});
