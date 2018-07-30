#!/usr/bin/env python3
# encoding: utf-8

import discord
from discord.ext import commands

with open('config.py') as f:
	config = eval(f.read(), {})

class Bot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned, **kwargs)
        for cog in config['cogs']:
               self.load_extension(cog)

    async def on_ready(self):
        print('Logged on as {0} (ID: {0.id})'.format(self.user))


bot = Bot()

if __name__ == '__main__':
	bot.run(config['tokens'].pop('discord'))
