#!/usr/bin/env python3

# © lambda#0987 <lambda@lambda.dance>
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64
import logging
import traceback

import discord
from bot_bin.bot import Bot
from discord.ext import commands
from utils.compat import md5

logging.basicConfig(level=logging.WARNING)
logging.getLogger('discord').setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# SelectorEventLoop on windows doesn't support subprocesses lol
import asyncio
import sys
if sys.platform == 'win32':
	loop = asyncio.ProactorEventLoop()
	asyncio.set_event_loop(loop)

class Bot(Bot):
	startup_extensions = (
		'cogs.emote',
		'cogs.meta',
		'bot_bin.debug',
		'bot_bin.misc',
		'bot_bin.systemd',
		'bot_bin.sql',
		'jishaku',
	)

	def __init__(self, **kwargs):
		with open('data/config.py', encoding='utf-8') as f:
			config = eval(f.read(), {})

		super().__init__(config=config, setup_db=True, **kwargs)
		# allow use of the bot's user ID before ready()
		token_part0 = self.config['tokens']['discord'].partition('.')[0].encode()
		self.user_id = int(base64.b64decode(token_part0 + b'=' * (3 - len(token_part0) % 3)))

	def process_config(self):
		"""Load the emojis from the config to be used when a command fails or succeeds
		We do it this way so that they can be used anywhere instead of requiring a bot instance.
		"""
		super().process_config()
		import utils.misc
		default = ('❌', '✅')
		utils.SUCCESS_EMOJIS = utils.misc.SUCCESS_EMOJIS = (
			self.config.get('response_emojis', {}).get('success', default))

	# Metrics

	async def on_command(self, ctx):
		user_id_md5 = md5(ctx.author.id.to_bytes(8, byteorder='big')).digest()
		await self.pool.execute(
			'INSERT INTO invokes (guild_id, user_id_md5, command) VALUES ($1, $2, $3)',
			getattr(ctx.guild, 'id', None), user_id_md5, ctx.command.qualified_name,
		)

	# we use on_shard_ready rather than on_ready because the latter is a bit less reliable
	async def on_shard_ready(self, shard_id):
		await self.pool.execute(
			"""
			INSERT INTO shard_info (shard_id, guild_count, member_count)
			VALUES ($1, $2, $3)
			ON CONFLICT (shard_id) DO UPDATE SET
				guild_count = EXCLUDED.guild_count,
				member_count = EXCLUDED.member_count
			""",
			shard_id, *self.shard_stats(shard_id),
		)

	async def update_shard(self, guild):
		await self.pool.execute(
			"""
			UPDATE shard_info
			SET
				guild_count = $2,
				member_count = $3
			WHERE shard_id = $1
			""",
			guild.shard_id, *self.shard_stats(guild.shard_id),
		)

	on_guild_join = on_guild_remove = update_shard

	def shard_stats(self, shard_id):
		guilds = [guild for guild in self.guilds if guild.shard_id == shard_id]
		guild_count = len(guilds)
		member_count = sum(getattr(guild, 'member_count', 0) for guild in guilds)
		return guild_count, member_count

def main():
	import sys

	if len(sys.argv) == 1:
		shard_count = None
		shard_ids = None
	elif len(sys.argv) < 3:
		print('Usage:', sys.argv[0], '[<shard count> <hyphen-separated list of shard IDs>]', file=sys.stderr)
		sys.exit(1)
	else:
		shard_count = int(sys.argv[1])
		shard_ids = list(map(int, sys.argv[2].split('-')))

	Bot(
		intents=discord.Intents(
			guilds=True,
			# we hardly need DM support but it's helpful to be able to run the help/support commands in DMs
			messages=True,
			# we don't need DM reactions because we don't ever paginate in DMs
			guild_reactions=True,
			emojis=True,
			# everything else, including `members` and `presences`, is implicitly false.
		),

		# the least stateful bot you will ever see 😎
		chunk_guilds_at_startup=False,
		member_cache_flags=discord.MemberCacheFlags.none(),
		# disable message cache
		max_messages=None,

		shard_count=shard_count,
		shard_ids=shard_ids,
	).run()

if __name__ == '__main__':
	main()
