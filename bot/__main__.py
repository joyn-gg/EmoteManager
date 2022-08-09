import os
import logging
import json

import discord

from bot.config import Config
from bot.tk_bot import TKBot

# Discord
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_SHARD_COUNT = os.environ["DISCORD_SHARD_COUNT"]
DISCORD_SHARD_IDS = os.environ["DISCORD_SHARD_IDS"]

# Bot
BOT_PREFIX = os.environ["BOT_PREFIX"]
BOT_VERSION = os.environ["BOT_VERSION"]
BOT_LOG_LEVEL = os.environ["BOT_LOG_LEVEL"]

if DISCORD_SHARD_COUNT:
    DISCORD_SHARD_COUNT = int(DISCORD_SHARD_COUNT)

if DISCORD_SHARD_IDS and json.loads(DISCORD_SHARD_IDS):
    DISCORD_SHARD_IDS = tuple(int(i) for i in json.loads(DISCORD_SHARD_IDS))
    assert DISCORD_SHARD_IDS
else:
    DISCORD_SHARD_IDS = None

DISCORD_ACTIVITY_MESSAGE = f"{BOT_PREFIX}help to get started"

config = Config(
    DEFAULT_PREFIX=BOT_PREFIX,
    DISCORD_TOKEN=DISCORD_TOKEN,

    SUCCESS_EMOJI="✅",   # Custom: "<:success:478164452261363712>",
    FAILURE_EMOJI="❌",   # Custom: "<:error:478164511879069707>",

    VERSION=BOT_VERSION,
    SUPPORT_LINK="https://discord.gg/tournamentkings",

    socks5_proxy_url=None,
    use_socks5_for_all_connections=False,
    user_agent='EmoteManagerBot (https://github.com/iomintz/emote-manager-bot)',
    ec_api_base_url=None,
    http_head_timeout=10,
    http_read_timeout=60
)

# Handle intents, this needs to match the dashboard in the Discord developer application portal
intents = discord.Intents.default()
intents.members = True

# Initialize logging
logging.basicConfig(
    level=BOT_LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

activity = discord.Activity(
    type=discord.ActivityType.playing,
    name=DISCORD_ACTIVITY_MESSAGE,
)

intents = discord.Intents(
    guilds=True,
    messages=True,
    guild_reactions=True,
    emojis=True,
)

bot = TKBot(
    intents=intents,
    config=config,
    activity=activity,
    shard_count=DISCORD_SHARD_COUNT,
    shard_ids=DISCORD_SHARD_IDS,
)


def main():
    cogs = (
        'cogs.emote',
        'cogs.meta',
        'bot_bin.debug',
        'bot_bin.misc',  # Ping & Uptime Command
        'bot_bin.systemd',
        'jishaku',  # Debug Command
    )
    for ext in cogs:
        logging.info(f"Loading {ext}...")
        bot.load_extension(ext)
    logging.info(f"Found {len(cogs)} extensions. Running...")
    bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
