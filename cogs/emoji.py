#!/usr/bin/env python3
# encoding: utf-8

from discord.ext import commands

class Emoji:
	def __init__(self, bot):
		self.bot = bot

	async def __local_check(self, context):
		return (
			context.guild
			and context.author.guild_permissions.manage_emojis)

def setup(bot):
	bot.add_cog(Emoji(bot))
