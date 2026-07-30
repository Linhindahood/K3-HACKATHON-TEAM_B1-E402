const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from codebase/.env or current directory
dotenv.config({ path: path.resolve(__dirname, '../.env') });
dotenv.config();

const { Client, GatewayIntentBits } = require('discord.js');

const DISCORD_BOT_TOKEN = process.env.DISCORD_BOT_TOKEN || '';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

client.once('ready', () => {
  console.log(`Bot đã đăng nhập: ${client.user ? client.user.tag : 'Client'} (backend: ${BACKEND_URL})`);
});

module.exports = {
  client,
  DISCORD_BOT_TOKEN,
  BACKEND_URL,
};
