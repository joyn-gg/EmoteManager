#!/usr/bin/env python3

# © 2018–2020 io mintz <io@mintz.cc>
#
# Emote Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Emote Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Emote Manager. If not, see <https://www.gnu.org/licenses/>.

import logging
import traceback

import discord
from bot_bin.bot import Bot
from discord.ext import commands

logging.basicConfig(level=logging.WARNING)
logging.getLogger('discord').setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Bot(Bot):
	startup_extensions = (
		'cogs.emote',
		'cogs.meta',
		'bot_bin.debug',
		'bot_bin.misc',
		'bot_bin.stats',
		'jishaku',
	)

	def __init__(self, **kwargs):
		with open('data/config.py') as f:
			config = eval(f.read(), {})

		super().__init__(config=config, **kwargs)

	def process_config(self):
		"""Load the emojis from the config to be used when a command fails or succeeds
		We do it this way so that they can be used anywhere instead of requiring a bot instance.
		"""
		super().process_config()
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
