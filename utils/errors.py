#!/usr/bin/env python3
# encoding: utf-8

from discord.ext.commands import CommandError


class EmojiManagerError(CommandError):
	"""Generic error with the bot. This can be used to catch all bot errors."""
	pass


class HTTPException(EmojiManagerError):
	"""The server did not respond with an OK status code."""
	def __init__(self, status):
		super().__init__(f'URL error: server returned error code {status}')


class EmojiNotFoundError(EmojiManagerError):
	"""An emoji with that name was not found"""
	def __init__(self, name):
		super().__init__(f'An emoji called `{name}` does not exist in this server.')


class InvalidImageError(EmojiManagerError):
	"""The image is not a GIF, PNG, or JPG"""
	def __init__(self):
		super().__init__('The image supplied was not a GIF, PNG, or JPG.')


class NoMoreSlotsError(EmojiManagerError):
	"""Raised in case all slots of a particular type (static/animated) are full"""
	def __init__(self):
		super().__init__('No more backend slots available.')


class PermissionDeniedError(EmojiManagerError):
	"""Raised when a user tries to modify an emoji without the Manage Emojis permission"""
	def __init__(self, name):
		super().__init__(f"You're not authorized to modify `{name}`.")


class DiscordError(Exception):
	"""Usually raised when the client cache is being baka"""
	def __init__(self):
		super().__init__('Discord seems to be having issues right now, please try again later.')
