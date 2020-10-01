# © 2018–2020 io mintz <io@mintz.cc>
#
# Emote Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Emote Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Emote Manager. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import contextlib
import typing

import discord
from discord.ext.commands import Context

# Copyright © 2016-2017 Pandentia and contributors
# https://github.com/Thessia/Liara/blob/75fa11948b8b2ea27842d8815a32e51ef280a999/cogs/utils/paginator.py

class Paginator:
	def __init__(self, ctx: Context, pages: typing.Iterable, *, timeout=300, delete_message=False,
				 delete_message_on_timeout=False, text_message=None):

		self.pages = list(pages)
		self.timeout = timeout
		self.author = ctx.author
		self.target = ctx.channel
		self.delete_msg = delete_message
		self.delete_msg_timeout = delete_message_on_timeout
		self.text_message = text_message

		self._stopped = None  # we use this later
		self._embed = None
		self._message = None
		self._client = ctx.bot

		self.footer = 'Page {} of {}'
		self.navigation = {
			'\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}': self.first_page,
			'\N{BLACK LEFT-POINTING TRIANGLE}': self.previous_page,
			'\N{BLACK RIGHT-POINTING TRIANGLE}': self.next_page,
			'\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}': self.last_page,
			'\N{BLACK SQUARE FOR STOP}': self.stop
		}

		self._page = None

	def react_check(self, reaction: discord.RawReactionActionEvent):
		if reaction.user_id != self.author.id:
			return False

		if reaction.message_id != self._message.id:
			return False

		target_emoji = str(reaction.emoji)
		return bool(discord.utils.find(lambda emoji: target_emoji == emoji, self.navigation))

	async def begin(self):
		"""Starts pagination"""
		self._stopped = False
		self._embed = discord.Embed()
		await self.first_page()
		for button in self.navigation:
			await self._message.add_reaction(button)
		while not self._stopped:
			try:
				reaction: RawReactionActionEvent = await self._client.wait_for(
					'raw_reaction_add',
					check=self.react_check,
					timeout=self.timeout)
			except asyncio.TimeoutError:
				await self.stop(delete=self.delete_msg_timeout)
				continue

			await self.navigation[str(reaction.emoji)]()

			await asyncio.sleep(0.2)
			with contextlib.suppress(discord.HTTPException):
				await self._message.remove_reaction(reaction.emoji, discord.Object(reaction.user_id))

	async def stop(self, *, delete=None):
		"""Aborts pagination."""
		if delete is None:
			delete = self.delete_msg

		if delete:
			with contextlib.suppress(discord.HTTPException):
				await self._message.delete()
		else:
			await self._clear_reactions()
		self._stopped = True

	async def _clear_reactions(self):
		try:
			await self._message.clear_reactions()
		except discord.Forbidden:
			for button in self.navigation:
				with contextlib.suppress(discord.HTTPException):
					await self._message.remove_reaction(button, self._message.author)
		except discord.HTTPException:
			pass

	async def format_page(self):
		self._embed.description = self.pages[self._page]
		self._embed.set_footer(text=self.footer.format(self._page + 1, len(self.pages)))

		kwargs = {'embed': self._embed}
		if self.text_message:
			kwargs['content'] = self.text_message

		if self._message:
			await self._message.edit(**kwargs)
		else:
			self._message = await self.target.send(**kwargs)

	async def first_page(self):
		self._page = 0
		await self.format_page()

	async def next_page(self):
		self._page += 1
		if self._page == len(self.pages):  # avoid the inevitable IndexError
			self._page = 0
		await self.format_page()

	async def previous_page(self):
		self._page -= 1
		if self._page < 0:	# ditto
			self._page = len(self.pages) - 1
		await self.format_page()

	async def last_page(self):
		self._page = len(self.pages) - 1
		await self.format_page()

class ListPaginator(Paginator):
	def __init__(self, ctx, _list: list, per_page=10, **kwargs):
		pages = []
		page = ''
		c = 0
		l = len(_list)
		for i in _list:
			if c > l:
				break
			if c % per_page == 0 and page:
				pages.append(page.strip())
				page = ''
			page += '{}. {}\n'.format(c+1, i)

			c += 1
		pages.append(page.strip())
		# shut up, IDEA
		# noinspection PyArgumentList
		super().__init__(ctx, pages, **kwargs)
		self.footer += ' ({} entries)'.format(l)
