#!/usr/bin/env python3
# encoding: utf-8

import discord

"""various utilities for use within the bot"""

"""Emotes used to indicate success/failure. You can obtain these from the discordbots.org guild,
but I uploaded them to my test server
so that both the staging and the stable versions of the bot can use them"""
SUCCESS_EMOTES = ('<:error:416845770239508512>', '<:success:416845760810844160>')

def format_user(bot, id, *, mention=False):
	"""Format a user ID for human readable display."""
	user = bot.get_user(id)
	if user is None:
		return f'Unknown user with ID {id}'
	# not mention: @null byte#8191 (140516693242937345)
	# mention: <@140516693242937345> (null byte#8191)
	# this allows people to still see the username and discrim
	# if they don't share a server with that user
	if mention:
		return f'{user.mention} (@{user})'
	else:
		return f'@{user} ({user.id})'

def format_http_exception(exception: discord.HTTPException):
	"""Formats a discord.HTTPException for relaying to the user.
	Sample return value:

	BAD REQUEST (status code: 400):
	Invalid Form Body
	In image: File cannot be larger than 256 kb.
	"""
	return (
		f'{exception.response.reason} (status code: {exception.response.status}):'
		f'\n{exception.text}')

def strip_angle_brackets(string):
	"""Strip leading < and trailing > from a string.
	Useful if a user sends you a url like <this> to avoid embeds, or to convert emotes to reactions."""
	if string.startswith('<') and string.endswith('>'):
		return string[1:-1]
	return string
