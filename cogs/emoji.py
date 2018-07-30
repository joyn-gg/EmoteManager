#!/usr/bin/env python3
# encoding: utf-8

import io
import imghdr
import asyncio
import logging
import weakref
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
import utils.image
from utils import errors
from utils.paginator import ListPaginator

class Emotes:
	def __init__(self, bot):
		self.bot = bot
		self.http = aiohttp.ClientSession(loop=self.bot.loop, read_timeout=30, headers={
			'User-Agent':
				self.bot.config['user_agent'] + ' '
				+ self.bot.http.user_agent
		})
		# keep track of paginators so we can end them when the cog is unloaded
		self.paginators = weakref.WeakSet()

	def __unload(self):
		self.bot.loop.create_task(self.http.close())

		async def stop_all_paginators():
			for paginator in self.paginators:
				await paginator.stop()

		self.bot.loop.create_task(stop_all_paginators())

	async def __local_check(self, context):
		if not context.guild:
			await context.send(
				f'{utils.SUCCESS_EMOTES[False]} Sorry, this command may only be used in a server.')
			return False

		if not context.author.guild_permissions.manage_emojis:
			await context.send(
				f'{utils.SUCCESS_EMOTES[False]} '
				"Sorry, you don't have enough permissions to run this command. "
				'You need the Manage Emojis permission.')
			return False

		return True

	async def on_command_error(self, context, error):
		if isinstance(error, errors.EmoteManagerError):
			await context.send(str(error))

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
		image_data = await self.bot.loop.run_in_executor(None, utils.image.resize_until_small, image_data)
		return await guild.create_custom_emoji(
			name=name,
			image=image_data.read(),
			reason=f'Created by {utils.format_user(self.bot, author_id)}')

	@commands.command()
	async def remove(self, context, name):
		emote = await self.disambiguate(context, name)
		await emote.delete(reason=f'Removed by {utils.format_user(self.bot, context.author.id)}')
		await context.send(f'Emote \:{emote.name}: successfully removed.')

	@commands.command()
	async def rename(self, context, old_name, new_name):
		emote = await self.disambiguate(context, old_name)
		try:
			await emote.edit(
				name=new_name,
				reason=f'Renamed by {utils.format_user(self.bot, context.author.id)}')
		except discord.HTTPException as ex:
			return await context.send(
				'An error occurred while renaming the emote:\n'
				+ utils.format_http_exception(ex))

		await context.send(f'Emote \:{old_name}: successfully renamed to \:{new_name}:')

	@commands.command()
	async def list(self, context):
		emotes = sorted(
			filter(lambda e: e.require_colons, context.guild.emojis),
			key=lambda e: e.name.lower())

		processed = []
		for emote in emotes:
			processed.append(f'{emote} (\:{emote.name}:)')

		paginator = ListPaginator(context, processed)
		self.paginators.add(paginator)
		await paginator.begin()

	async def disambiguate(self, context, name):
		candidates = [e for e in context.guild.emojis if e.name.lower() == name.lower() and e.require_colons]
		if not candidates:
			raise errors.EmoteNotFoundError(name)

		if len(candidates) == 1:
			return candidates[0]

		message = ['Multiple emotes were found with that name. Which one do you mean?']
		for i, emote in enumerate(candidates, 1):
			message.append(f'{i}. {emote} (\:{emote.name}:)')

		await context.send('\n'.join(message))

		def check(message):
			try:
				int(message.content)
			except ValueError:
				return False
			else:
				return message.author == context.author

		try:
			message = await self.bot.wait_for('message', check=check, timeout=30)
		except asyncio.TimeoutError:
			raise commands.UserInputError('Sorry, you took too long. Try again.')

		return candidates[int(message.content)-1]


def setup(bot):
	bot.add_cog(Emotes(bot))
