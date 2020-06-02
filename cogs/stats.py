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

import collections
import json

from discord.ext import commands
from bot_bin.stats import BotBinStats

class Stats(BotBinStats):
	path = 'data/guild_counts.json'

	@commands.Cog.listener()
	async def on_ready(self):
		with open(self.path, 'w+') as f:
			contents = f.read()
			if contents:
				guild_counts = json.loads(contents)
			else:
				guild_counts = {}

			my_counts = collections.Counter()

			for guild in self.bot.guilds:
				my_counts[str(guild.shard_id)] += 1

			guild_counts.update(my_counts)

			f.seek(0)
			json.dump(guild_counts, f)

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		self.incr_guild_count(guild.shard_id, +1)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		self.incr_guild_count(guild.shard_id, -1)

	def incr_guild_count(self, shard_id, amount):
		with open(self.path, 'w+') as f:
			guild_counts = json.load(f)
			guild_counts[str(shard_id)] += amount
			f.seek(0)
			json.dump(guild_counts, f)

	async def guild_count(self):
		with open(self.path) as f:
			return sum(json.load(f).values())

def setup(bot):
	bot.add_cog(Stats(bot))
