const { EmbedBuilder, AttachmentBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

/**
 * Hậu xử lý sạch văn bản: Loại bỏ marker [S1], [S2]... và khối "Nguồn tham khảo:..." bằng Regex
 * @param {string} text - Văn bản gốc từ backend
 * @returns {string} - Văn bản đã làm sạch cho hiển thị người dùng
 */
function cleanAnswer(text) {
  if (!text) return '';
  let cleaned = text;

  // 1. Loại bỏ khối "Nguồn tham khảo: ..." ở cuối câu trả lời (nếu có)
  cleaned = cleaned.replace(/\n\s*Nguồn tham khảo:\s*[\s\S]*$/i, '');

  // 2. Loại bỏ các marker trích dẫn [S1], [S2], [S3]... trong văn bản
  cleaned = cleaned.replace(/\s*\[S\d+\]/g, '');

  // 3. Chuẩn hóa khoảng trắng dư thừa trước dấu chấm/phẩy
  cleaned = cleaned.replace(/[ \t]+\./g, '.').replace(/[ \t]+,/g, ',');

  return cleaned.trim();
}

/**
 * Format câu trả lời backend thành Discord embed sạch đẹp (không hiện trích dẫn nội bộ).
 * @param {string} answer - Nội dung câu trả lời
 * @param {string[]} sources - Danh sách nguồn (chỉ dùng nội bộ audit, không render ra Discord)
 * @param {Array<object>} media - Danh sách media assets (ảnh bản đồ...)
 * @param {string} intent - Intent câu hỏi từ router
 * @returns {{ embed: EmbedBuilder, files: AttachmentBuilder[] }}
 */
function formatAnswer(answer, sources = [], media = [], intent = '') {
  const embed = new EmbedBuilder()
    .setColor(0x0088FF)
    .setFooter({ text: 'VinAI Support Assistant • Thông tin chính thức' });

  // Đặt tiêu đề dựa theo Intent
  if (intent === 'greeting') {
    embed.setTitle('👋 Chào bạn!');
  } else if (intent === 'identity') {
    embed.setTitle('🤖 Trợ lý VinAI');
  } else if (intent === 'help') {
    embed.setTitle('💡 Hướng dẫn & Dịch vụ hỗ trợ');
  } else if (intent === 'unsupported_action') {
    embed.setTitle('⚠️ Lưu ý hướng dẫn thao tác');
  } else if (intent === 'out_of_scope') {
    embed.setTitle('ℹ️ Phạm vi hỗ trợ');
  } else {
    embed.setTitle('📌 Thông tin tra cứu');
  }

  // Làm sạch văn bản trước khi đặt vào Description (bỏ [S1], [S2] và Nguồn tham khảo)
  const cleanedText = cleanAnswer(answer);
  embed.setDescription(cleanedText || '_Không có nội dung trả lời._');

  const files = [];

  // Xử lý đính kèm ảnh bản đồ / Media assets (nếu có)
  if (media && Array.isArray(media) && media.length > 0) {
    for (const item of media) {
      const filename = item.local_path || '1_map.png';
      const rawPath = path.resolve(__dirname, '../backend/knowledge_base/raw', filename);
      if (fs.existsSync(rawPath)) {
        const attachment = new AttachmentBuilder(rawPath, { name: filename });
        files.push(attachment);
        embed.setImage(`attachment://${filename}`);
      }

      // Thêm link bản đồ trực tuyến
      if (item.url) {
        embed.addFields({
          name: '🌐 Bản đồ trực tuyến',
          value: `[${item.title || 'Xem vị trí cơ sở vật chất'}](${item.url})`,
          inline: false,
        });
      }
    }
  }

  return { embed, files };
}

module.exports = {
  cleanAnswer,
  formatAnswer,
};
