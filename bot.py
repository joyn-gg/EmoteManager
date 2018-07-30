#!/usr/bin/env python3
# encoding: utf-8

import logging
import traceback

import discord
from discord.ext import commands

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Bot(commands.AutoShardedBot):
	def __init__(self, **kwargs):
		super().__init__(command_prefix=commands.when_mentioned, **kwargs)

		with open('config.py') as f:
			self.config = eval(f.read(), {})

		for cog in self.config['cogs']:
			   self.load_extension(cog)

	def run(self):
		super().run(self.config['tokens'].pop('discord'))

	async def on_ready(self):
		logger.info('Logged on as {0} (ID: {0.id})'.format(self.user))

	async def on_message(self, message):
		if message.author.bot:
			return

		await self.process_commands(message)

	# https://github.com/Rapptz/RoboDanny/blob/ca75fae7de132e55270e53d89bc19dd2958c2ae0/bot.py#L77-L85
	async def on_command_error(self, context, error):
		if isinstance(error, commands.NoPrivateMessage):
			await context.author.send('This command cannot be used in private messages.')
		elif isinstance(error, commands.DisabledCommand):
			message = 'Sorry. This command is disabled and cannot be used.'
			try:
				await context.author.send(message)
			except discord.Forbidden:
				await context.send(message)
		elif isinstance(error, commands.UserInputError):
			await context.send(error)
		elif isinstance(error, commands.NotOwner):
			logger.error('%s tried to run %s but is not the owner', context.author, context.command.name)
		elif isinstance(error, commands.CommandInvokeError):
			await context.send('An internal error occured while trying to run that command.')

			logger.error('In %s:', context.command.qualified_name)
			logger.error(''.join(traceback.format_tb(error.original.__traceback__)))
			# pylint: disable=logging-format-interpolation
			logger.error('{0.__class__.__name__}: {0}'.format(error.original))

bot = Bot()

if __name__ == '__main__':
	bot.run()
