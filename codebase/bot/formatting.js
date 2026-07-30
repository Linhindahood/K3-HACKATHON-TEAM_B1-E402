const { EmbedBuilder } = require('discord.js');

/**
 * Format câu trả lời backend thành Discord embed.
 * @param {string} answer
 * @param {string[]} sources
 * @returns {EmbedBuilder}
 */
function formatAnswer(answer, sources) {
  const embed = new EmbedBuilder()
    .setDescription(answer || '')
    .setColor(0x0099FF);

  if (sources && Array.isArray(sources) && sources.length > 0) {
    embed.addFields({
      name: 'Nguồn',
      value: sources.map((s) => `- ${s}`).join('\n'),
      inline: false,
    });
  }

  return embed;
}

module.exports = {
  formatAnswer,
};
