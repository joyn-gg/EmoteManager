#!/usr/bin/env python3
# encoding: utf-8

import io
import imghdr
import asyncio
import logging
import traceback
import contextlib

logger = logging.getLogger(__name__)

try:
	from wand.image import Image
except ImportError:
	logger.warn('failed to import wand.image. Image manipulation functions will be unavailable.')
	Image = None

import aiohttp
import discord
from discord.ext import commands

import utils
from utils import errors

class Emoji:
	def __init__(self, bot):
		self.bot = bot
		self.http = aiohttp.ClientSession(loop=self.bot.loop, read_timeout=30, headers={
			'User-Agent':
				self.bot.config['user_agent'] + ' '
				+ self.bot.http.user_agent
		})
	async def __local_check(self, context):
		return (
			context.guild
			and context.author.guild_permissions.manage_emojis)

	@commands.command()
	async def add(self, context, *args):
		"""Adds an emoji to this server."""
		try:
			name, url = self.parse_add_command_args(context, args)
		except commands.BadArgument as exception:
			return await context.send(exception)

		async with context.typing():
			message = await self.add_safe(context.guild, name, url, context.message.author.id)
		await context.send(message)

	@classmethod
	def parse_add_command_args(cls, context, args):
		if context.message.attachments:
			return cls.parse_add_command_attachment(context, args)

		elif len(args) == 1:
			match = utils.emote.RE_CUSTOM_EMOTE.match(args[0])
			if match is None:
				raise commands.BadArgument(
					'Error: I expected a custom emote as the first argument, '
					'but I got something else. '
					"If you're trying to add an emote using an image URL, "
					'you need to provide a name as the first argument, like this:\n'
					'`{}add NAME_HERE URL_HERE`'.format(context.prefix))
			else:
				animated, name, id = match.groups()
				url = utils.emote.url(id, animated=animated)

			return name, url

		elif len(args) >= 2:
			name = args[0]
			match = utils.emote.RE_CUSTOM_EMOTE.match(args[1])
			if match is None:
				url = utils.strip_angle_brackets(args[1])
			else:
				url = utils.emote.url(match.group('id'))

			return name, url

		elif not args:
			raise commands.BadArgument('Your message had no emotes and no name!')

	@staticmethod
	def parse_add_command_attachment(context, args):
		attachment = context.message.attachments[0]
		# as far as i can tell, this is how discord replaces filenames when you upload an emote image
		name = ''.join(args) if args else attachment.filename.split('.')[0].replace(' ', '')
		url = attachment.url

		return name, url

	async def add_safe(self, guild, name, url, author_id):
		"""Try to add an emote. Returns a string that should be sent to the user."""
		try:
			emote = await self.add_from_url(guild, name, url, author_id)
		except discord.HTTPException as ex:
			logger.error(traceback.format_exc())
			return (
				'An error occurred while creating the emote:\n'
				+ utils.format_http_exception(ex))
		except asyncio.TimeoutError:
			return 'Error: retrieving the image took too long.'
		except ValueError:
			return 'Error: Invalid URL.'
		else:
			return f'Emote {emote} successfully created.'

	async def add_from_url(self, guild, name, url, author_id):
		image_data = await self.fetch_emote(url)
		emote = await self.create_emote_from_bytes(guild, name, author_id, image_data)

		return emote

	async def fetch_emote(self, url):
		# credits to @Liara#0001 (ID 136900814408122368) for most of this part
		# https://gitlab.com/Pandentia/element-zero/blob/47bc8eeeecc7d353ec66e1ef5235adab98ca9635/element_zero/cogs/emoji.py#L217-228
		async with self.http.head(url, timeout=5) as response:
			if response.reason != 'OK':
				raise errors.HTTPException(response.status)
			if response.headers.get('Content-Type') not in ('image/png', 'image/jpeg', 'image/gif'):
				raise errors.InvalidImageError

		async with self.http.get(url) as response:
			if response.reason != 'OK':
				raise errors.HTTPException(response.status)
			return io.BytesIO(await response.read())

	async def create_emote_from_bytes(self, guild, name, author_id, image_data: io.BytesIO):
		# resize_until_small is normally blocking, because wand is.
		# run_in_executor is magic that makes it non blocking somehow.
		# also, None as the executor arg means "use the loop's default executor"
		image_data = await self.bot.loop.run_in_executor(None, self.resize_until_small, image_data)
		return await guild.create_custom_emoji(
			name=name,
			image=image_data.read(),
			reason=f'Created by {utils.format_user(self.bot, author_id)}')

	@staticmethod
	def is_animated(image_data: bytes):
		"""Return whether the image data is animated, or raise InvalidImageError if it's not an image."""
		type = imghdr.what(None, image_data)
		if type == 'gif':
			return True
		elif type in ('png', 'jpeg'):
			return False
		else:
			raise errors.InvalidImageError

	@classmethod
	def size(cls, data: io.BytesIO):
		"""return the size, in bytes, of the data a BytesIO object represents"""
		with cls.preserve_position(data):
			data.seek(0, io.SEEK_END)
			return data.tell()

	class preserve_position(contextlib.AbstractContextManager):
		def __init__(self, fp):
			self.fp = fp
			self.old_pos = fp.tell()

		def __exit__(self, *excinfo):
			self.fp.seek(self.old_pos)

	@classmethod
	def resize_until_small(cls, image_data: io.BytesIO):
		"""If the image_data is bigger than 256KB, resize it until it's not"""
		# It's important that we only attempt to resize the image when we have to,
		# ie when it exceeds the Discord limit of 256KiB.
		# Apparently some <256KiB images become larger when we attempt to resize them,
		# so resizing sometimes does more harm than good.
		max_resolution = 128  # pixels
		size = cls.size(image_data)
		while size > 256 * 2**10 and max_resolution >= 32:  # don't resize past 32x32 or 256KiB
			logger.debug('image size too big (%s bytes)', size)
			logger.debug('attempting resize to %s*%s pixels', max_resolution, max_resolution)
			image_data = cls.thumbnail(image_data, (max_resolution, max_resolution))
			size = cls.size(image_data)
			max_resolution //= 2
		return image_data

	@classmethod
	def thumbnail(cls, image_data: io.BytesIO, max_size=(128, 128)):
		"""Resize an image in place to no more than max_size pixels, preserving aspect ratio."""
		# Credit to @Liara#0001 (ID 136900814408122368)
		# https://gitlab.com/Pandentia/element-zero/blob/47bc8eeeecc7d353ec66e1ef5235adab98ca9635/element_zero/cogs/emoji.py#L243-247
		image = Image(blob=image_data)
		image.resize(*cls.scale_resolution((image.width, image.height), max_size))
		# we create a new buffer here because there's wand errors otherwise.
		# specific error:
		# MissingDelegateError: no decode delegate for this image format `' @ error/blob.c/BlobToImage/353
		out = io.BytesIO()
		image.save(file=out)
		out.seek(0)
		return out

	@staticmethod
	def scale_resolution(old_res, new_res):
		# https://stackoverflow.com/a/6565988
		"""Resize a resolution, preserving aspect ratio. Returned w,h will be <= new_res"""
		old_width, old_height = old_res
		new_width, new_height = new_res
		old_ratio = old_width / old_height
		new_ratio = new_width / new_height
		if new_ratio > old_ratio:
			return (old_width * new_height//old_height, new_height)
		return new_width, old_height * new_width//old_width



def setup(bot):
	bot.add_cog(Emoji(bot))
