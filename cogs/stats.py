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

# The resource tracker unlinks shared memory on shutdown and assumes all processes that share memory
# share a parent python process. But this is not necessarily the case: the user might decide to run
# each cluster as a systemd unit for example. We don't want a crash of a single cluster to unlink
# the shared memory segment, so we stub out the resource tracking process here,
# as there's no built in way to disable it.
# See https://bugs.python.org/issue38119
from multiprocessing import resource_tracker
resource_tracker.ensure_running = lambda: None
resource_tracker.main = lambda: None

class Stats(BotBinStats):
	def __init__(self, bot):
		super().__init__(bot)

		# Use our user ID as part of the shm name
		# to allow running multiple instances of the bot on the same machine.
		shm_name = f'emote-manager-{self.bot.user_id}'
		if self.is_opener():
			seq = [0] * self.bot.shard_count
			try:
				self.shlist = ShareableList(seq, name=shm_name)
			except FileExistsError:
				# The file was probably left open from a previous run of the bot,
				# so let's re-attach and wipe the old data.
				self.shlist = ShareableList(name=shm_name)
				# apparently ShareableLists don't support slicing with None values of `stop`
				self.shlist[:self.bot.shard_count] = seq
		else:
			try:
				self.shlist = ShareableList(name=shm_name)
			except FileNotFoundError:
				# looks like we're the first cluster to start up
				seq = [0] * self.bot.shard_count
				self.shlist = ShareableList(seq, name=shm_name)

		self.count()

	def is_opener(self):
		"""return whether this is the cluster that should open the shared memory"""
		return 0 in self.bot.shard_ids

	def is_reporter(self):
		"""return whether this is the cluster that should report stats to the bot lists"""
		return self.bot.shard_count - 1 in self.bot.shard_ids

	def cog_unload(self):
		self.shlist.shm.close()
		if self.is_opener():
			self.shlist.shm.unlink()

	@commands.Cog.listener()
	async def on_ready(self):
		self.count()
		if self.is_reporter():
			await self.send()

	def count(self):
		for shard_id in self.bot.shard_ids:
			self.shlist[shard_id] = 0

		for guild in self.bot.guilds:
			self.shlist[guild.shard_id] += 1

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
