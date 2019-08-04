import asyncio

from discord.ext import commands

import utils

class MissingManageEmojisPermission(commands.MissingPermissions):
	"""The invoker or the bot doesn't have permissions to manage server emojis."""

	def __init__(self):
		super(Exception, self).__init__(
			f'{utils.SUCCESS_EMOJIS[False]} '
			"Sorry, you don't have enough permissions to run this command. "
			'You and I both need the Manage Emojis permission.')

class EmoteManagerError(commands.CommandError):
	"""Generic error with the bot. This can be used to catch all bot errors."""
	pass

class ImageResizeTimeoutError(EmoteManagerError, asyncio.TimeoutError):
	"""Resizing the image took too long."""
	def __init__(self):
		super().__init__('Error: resizing the image took too long.')

class HTTPException(EmoteManagerError):
	"""The server did not respond with an OK status code."""
	def __init__(self, status):
		super().__init__(f'URL error: server returned error code {status}')

class EmoteNotFoundError(EmoteManagerError):
	"""An emote with that name was not found"""
	def __init__(self, name):
		super().__init__(f'An emote called `{name}` does not exist in this server.')

class FileTooBigError(EmoteManagerError):
	def __init__(self, size, limit):
		self.size = size
		self.limit = limit

class InvalidFileError(EmoteManagerError):
	"""The file is not a zip, tar, GIF, PNG, or JPG file."""
	def __init__(self):
		super().__init__('Invalid file given.')

class InvalidImageError(InvalidFileError):
	"""The image is not a GIF, PNG, or JPG"""
	def __init__(self):
		super(Exception, self).__init__('The image supplied was not a GIF, PNG, or JPG.')

class PermissionDeniedError(EmoteManagerError):
	"""Raised when a user tries to modify an emote without the Manage Emojis permission"""
	def __init__(self, name):
		super().__init__(f"You're not authorized to modify `{name}`.")

class DiscordError(Exception):
	"""Usually raised when the client cache is being baka"""
	def __init__(self):
		super().__init__('Discord seems to be having issues right now, please try again later.')
