/**
 * Logger ghi lại câu hỏi & câu trả lời ra file JSON Lines (.jsonl).
 *
 * Mỗi dòng trong file log là một JSON object chứa đầy đủ thông tin:
 * timestamp, user Discord, channel, guild, question, answer, sources, response_time_ms, status.
 *
 * Sử dụng: const { logQA } = require('./logger');
 */
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, 'logs');
const LOG_FILE = path.join(LOG_DIR, 'qa_log.jsonl');

// Tạo thư mục logs nếu chưa có
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

/**
 * Ghi một dòng log Q&A vào file .jsonl.
 *
 * @param {object} entry
 * @param {import('discord.js').Message} entry.message - Discord message object
 * @param {string} entry.question - Câu hỏi đã được xử lý (bỏ mention)
 * @param {string} [entry.answer] - Câu trả lời từ backend
 * @param {string[]} [entry.sources] - Danh sách nguồn tham khảo
 * @param {boolean} [entry.hasEvidence] - Có bằng chứng từ tài liệu không
 * @param {number} [entry.responseTimeMs] - Thời gian xử lý (ms)
 * @param {'success'|'error'} entry.status - Trạng thái xử lý
 * @param {string} [entry.error] - Thông tin lỗi (nếu có)
 */
function logQA(entry) {
  const { message, question, answer, sources, hasEvidence, responseTimeMs, status, error } = entry;

  const logEntry = {
    timestamp: new Date().toISOString(),
    user: {
      tag: message.author.tag,
      id: message.author.id,
      username: message.author.username,
    },
    channel: {
      name: message.channel.name || 'DM',
      id: message.channel.id,
    },
    guild: message.guild
      ? { name: message.guild.name, id: message.guild.id }
      : null,
    question,
    answer: answer || null,
    sources: sources || [],
    has_evidence: hasEvidence ?? null,
    response_time_ms: responseTimeMs ?? null,
    status,
  };

  if (error) {
    logEntry.error = error;
  }

  const line = JSON.stringify(logEntry) + '\n';

  fs.appendFile(LOG_FILE, line, (err) => {
    if (err) {
      console.error('Lỗi ghi log Q&A:', err);
    }
  });
}

module.exports = { logQA, LOG_FILE };
