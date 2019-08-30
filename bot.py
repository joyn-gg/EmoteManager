#!/usr/bin/env python3
# encoding: utf-8

import logging
import traceback

import discord
from ben_cogs.bot import BenCogsBot
from discord.ext import commands

logging.basicConfig(level=logging.WARNING)
logging.getLogger('discord').setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Bot(BenCogsBot):
	startup_extensions = (
		'cogs.emote',
		'cogs.meta',
		'ben_cogs.debug',
		'ben_cogs.misc',
		'ben_cogs.stats',
		'jishaku',
	)

	def __init__(self, **kwargs):
		with open('config.py') as f:
			config = eval(f.read(), {})

		super().__init__(config=config, **kwargs)
		self._setup_success_emojis()

	def _setup_success_emojis(self):
		"""Load the emojis from the config to be used when a command fails or succeeds
		We do it this way so that they can be used anywhere instead of requiring a bot instance.
		"""
		import utils.misc
		default = ('❌', '✅')
		utils.SUCCESS_EMOJIS = utils.misc.SUCCESS_EMOJIS = (
			self.config.get('response_emojis', {}).get('success', default))

	def initial_activity(self):
		if not self.is_ready():
			return super().activity
		return super().activity or discord.Game(f'@{self.user.name} help')

if __name__ == '__main__':
	Bot().run()
