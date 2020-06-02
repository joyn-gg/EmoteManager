# © 2020 io mintz <io@mintz.cc>
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

from multiprocessing.shared_memory import ShareableList

from discord.ext import commands
from bot_bin.stats import BotBinStats

class Stats(BotBinStats):
	def __init__(self, bot):
		super().__init__(bot)
		seq = [0] * self.bot.shard_count if self.is_opener() else None
		# Use our user ID as part of the shm name to allow running multiple instances of the bot on the same machine.
		# on_ready() hasn't run yet, so we don't have self.bot.user.
		token = self.bot.config['tokens']['discord']
		user_id = token.partition('.')[0]
		self.shlist = ShareableList(seq, name=f'emote-manager-{user_id}')

	def is_opener(self):
		"""return whether this is the process that should open the shared memory"""
		return 0 in self.bot.shard_ids

	def is_reporter(self):
		"""return whether we should report stats to the bot lists"""
		return self.bot.shard_count - 1 in self.bot.shard_ids

	def cog_unload(self):
		self.shlist.shm.close()
		if self.is_opener():
			self.shlist.shm.unlink()

	@commands.Cog.listener()
	async def on_ready(self):
		for guild in self.bot.guilds:
			self.shlist[guild.shard_id] += 1

		if self.is_reporter():
			await self.send()

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		self.shlist[guild.shard_id] += 1

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		self.shlist[guild.shard_id] -= 1

	async def guild_count(self):
		return sum(self.shlist)

def setup(bot):
	bot.add_cog(Stats(bot))
