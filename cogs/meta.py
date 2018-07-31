#!/usr/bin/env python3
# encoding: utf-8

import discord
from discord.ext import commands


class Meta:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['inv'])
	async def invite(self, context):
		"""Gives you a link to add me to your server."""
		permissions = discord.Permissions()
		permissions.update(**dict.fromkeys((
			'read_messages',
			'send_messages',
			'add_reactions',
			'external_emojis',
			'manage_emojis',
			'embed_links',
		), True))

		await context.send('<%s>' % discord.utils.oauth_url(self.bot.user.id, permissions))

def setup(bot):
	bot.add_cog(Meta(bot))
