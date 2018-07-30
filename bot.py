#!/usr/bin/env python3
# encoding: utf-8

import discord
from discord.ext import commands

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
		print('Logged on as {0} (ID: {0.id})'.format(self.user))


bot = Bot()

if __name__ == '__main__':
	bot.run()
