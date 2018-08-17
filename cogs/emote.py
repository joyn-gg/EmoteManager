#!/usr/bin/env python3
# encoding: utf-8

import io
import imghdr
import asyncio
import logging
import weakref
import traceback
import contextlib
import urllib.parse

import aioec
import aiohttp
import discord
from discord.ext import commands

import utils
import utils.image
from utils import errors
from utils.paginator import ListPaginator

logger = logging.getLogger(__name__)

class Emotes:
	def __init__(self, bot):
		self.bot = bot
		self.http = aiohttp.ClientSession(loop=self.bot.loop, read_timeout=30, headers={
			'User-Agent':
				self.bot.config['user_agent'] + ' '
				+ self.bot.http.user_agent
		})
		self.aioec = aioec.Client(loop=self.bot.loop)
		# keep track of paginators so we can end them when the cog is unloaded
		self.paginators = weakref.WeakSet()

	def __unload(self):
		self.bot.loop.create_task(self.http.close())
		self.bot.loop.create_task(self.aioec.close())

		async def stop_all_paginators():
			for paginator in self.paginators:
				await paginator.stop()

		self.bot.loop.create_task(stop_all_paginators())

	async def __local_check(self, context):
		if not context.guild:
			raise commands.NoPrivateMessage

		if context.command is self.list:
			return True

		if (
			not context.author.guild_permissions.manage_emojis
			or not context.guild.me.guild_permissions.manage_emojis
		):
			raise errors.MissingManageEmojisPermission

		return True

	async def on_command_error(self, context, error):
		if isinstance(error, (errors.EmoteManagerError, errors.MissingManageEmojisPermission)):
			await context.send(str(error))

		if isinstance(error, commands.NoPrivateMessage):
			await context.send(
				f'{utils.SUCCESS_EMOTES[False]} Sorry, this command may only be used in a server.')

	@commands.command()
	async def add(self, context, *args):
		"""Add a new emote to this server.

		You can use it like this:
		`add :thonkang:` (if you already have that emote)
		`add rollsafe https://image.noelshack.com/fichiers/2017/06/1486495269-rollsafe.png`
		`add speedtest <https://cdn.discordapp.com/emojis/379127000398430219.png>`

		With a file attachment:
		`add name` will upload a new emote using the first attachment as the image and call it `name`
		`add` will upload a new emote using the first attachment as the image,
		and its filename as the name
		"""
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

	@commands.command(name='add-from-ec', aliases=['addfromec'])
	async def add_from_ec(self, context, name):
		"""Copies an emote from Emoji Connoisseur to your server.

		The list of possible emotes you can copy is here:
		https://emoji-connoissuer.python-for.life/list
		"""
		name = name.strip(':')
		try:
			emote = await self.aioec.emote(name)
		except aioec.NotFound:
			return await context.send("Emote not found in Emoji Connoisseur's database.")
		except aioec.HttpException as exception:
			return await context.send(
				f'Error: the Emoji Connoisseur API returned status code {exception.status}')

		reason = (
			f'Added from Emoji Connoisseur by {utils.format_user(self.bot, context.author.id)}. '
			f'Original emote author: {utils.format_user(self.bot, emote.author)}')

		async with context.typing():
			message = await self.add_safe(context.guild, name, utils.emote.url(
				emote.id, animated=emote.animated
			), context.author.id, reason=reason)

		await context.send(message)

	async def add_safe(self, guild, name, url, author_id, *, reason=None):
		"""Try to add an emote. Returns a string that should be sent to the user."""
		try:
			emote = await self.add_from_url(guild, name, url, author_id, reason=reason)
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

	async def add_from_url(self, guild, name, url, author_id, *, reason=None):
		image_data = await self.fetch_emote(url)
		emote = await self.create_emote_from_bytes(guild, name, author_id, image_data, reason=reason)

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

	async def create_emote_from_bytes(self, guild, name, author_id, image_data: io.BytesIO, *, reason=None):
		# resize_until_small is normally blocking, because wand is.
		# run_in_executor is magic that makes it non blocking somehow.
		# also, None as the executor arg means "use the loop's default executor"
		image_data = await self.bot.loop.run_in_executor(None, utils.image.resize_until_small, image_data)
		if reason is None:
			reason = f'Created by {utils.format_user(self.bot, author_id)}'
		return await guild.create_custom_emoji(
			name=name,
			image=image_data.read(),
			reason=reason)

	@commands.command(aliases=('delete', 'delet', 'rm'))
	async def remove(self, context, *emotes):
		"""Remove an emote from this server.

		emotes: the name of an emote or of one or more emotes you'd like to remove.
		"""
		if len(emotes) == 1:
			emote = await self.parse_emote(context, emotes[0])
			await emote.delete(reason=f'Removed by {utils.format_user(self.bot, context.author.id)}')
			await context.send(f'Emote \:{emote.name}: successfully removed.')
		else:
			for emote in emotes:
				await context.invoke(self.remove, emote)
			with contextlib.suppress(discord.HTTPException):
				await context.message.add_reaction('✅')

	@commands.command(aliases=('mv',))
	async def rename(self, context, old, new_name):
		"""Rename an emote on this server.

		old: the name of the emote to rename, or the emote itself
		new_name: what you'd like to rename it to
		"""
		emote = await self.parse_emote(context, old)
		try:
			await emote.edit(
				name=new_name,
				reason=f'Renamed by {utils.format_user(self.bot, context.author.id)}')
		except discord.HTTPException as ex:
			return await context.send(
				'An error occurred while renaming the emote:\n'
				+ utils.format_http_exception(ex))

		await context.send(f'Emote successfully renamed to \:{new_name}:')

	@commands.command(aliases=('ls', 'dir'))
	async def list(self, context):
		"""A list of all emotes on this server.

		The list shows each emote and its raw form.
		"""
		emotes = sorted(
			filter(lambda e: e.require_colons, context.guild.emojis),
			key=lambda e: e.name.lower())

		processed = []
		for emote in emotes:
			raw = str(emote).replace(':', '\:')
			processed.append(f'{emote} {raw}')

		paginator = ListPaginator(context, processed)
		self.paginators.add(paginator)
		await paginator.begin()

	async def parse_emote(self, context, name_or_emote):
		match = utils.emote.RE_CUSTOM_EMOTE.match(name_or_emote)
		if match:
			id = int(match.group('id'))
			emote = discord.utils.get(context.guild.emojis, id=id)
			if emote:
				return emote
		name = name_or_emote
		return await self.disambiguate(context, name)

	async def disambiguate(self, context, name):
		name = name.strip(':')  # in case the user tries :foo: and foo is animated
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
