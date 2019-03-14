#!/usr/bin/env python3
# encoding: utf-8

import contextlib

import discord
from discord.ext import commands

class Meta(commands.Cog):
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

	@commands.command()
	async def support(self, context):
		"""Directs you to the support server."""
		try:
			await context.author.send(self.bot.config['support_server_invite'])
			with contextlib.suppress(discord.HTTPException):
				await context.message.add_reaction('📬')  # TODO make this emoji configurable too
		except discord.Forbidden:
			with contextlib.suppress(discord.HTTPException):
				await context.message.add_reaction(utils.SUCCESS_EMOJIS[True])
			await context.send('Unable to send invite in DMs. Please allow DMs from server members.')

def setup(bot):
	bot.add_cog(Meta(bot))

	if not bot.config.get('support_server_invite'):
		bot.remove_command('support')
