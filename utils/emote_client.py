# © lambda#0987
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys
import json
import asyncio
import aiohttp
import platform
import datetime
import urllib.parse
from typing import Dict
from http import HTTPStatus
import utils.image as image_utils
from utils.errors import RateLimitedError
from discord import HTTPException, Forbidden, NotFound, DiscordServerError

class GuildRetryTimes:
	"""Holds the times, for a particular guild,
	that we have to wait until for the rate limit for a particular HTTP method to elapse.
	"""
	__slots__ = frozenset({'POST', 'DELETE'})

	def __init__(self, POST=None, DELETE=None):
		self.POST = POST
		self.DELETE = DELETE

	def validate(self):
		now = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
		if self.POST and self.POST < now:
			self.POST = None
		if self.DELETE and self.DELETE < now:
			self.DELETE = None
		return self.POST or self.DELETE

GuildId = int

async def json_or_text(resp):
	text = await resp.text(encoding='utf-8')
	try:
		if resp.headers['content-type'] == 'application/json':
			return json.loads(text)
	except KeyError:
		# Thanks Cloudflare
		pass

	return text

class EmoteClient:
	BASE_URL = 'https://discord.com/api/v7'
	HTTP_ERROR_CLASSES = {
		HTTPStatus.FORBIDDEN: Forbidden,
		HTTPStatus.NOT_FOUND: NotFound,
		HTTPStatus.SERVICE_UNAVAILABLE: DiscordServerError,
	}

	def __init__(self, *, token):
		self.guild_rls: Dict[GuildId, GuildRetryTimes] = {}
		user_agent = (
			'EmoteManager-EmoteClient; '
			f'aiohttp/{aiohttp.__version__}; '
			f'{platform.python_implementation()}/{".".join(map(str, sys.version_info))}'
		)
		self.http = aiohttp.ClientSession(headers={
			'User-Agent': user_agent,
			'Authorization': 'Bot ' + token,
			'X-Ratelimit-Precision': 'millisecond',
		})

	async def request(self, method, path, guild_id, **kwargs):
		self._check_rl(method, guild_id)

		headers = {}
		# Emote Manager shouldn't use walrus op until Debian adopts 3.8 :(
		reason = kwargs.pop('reason', None)
		if reason:
			headers['X-Audit-Log-Reason'] = urllib.parse.quote(reason, safe='/ ')
		kwargs['headers'] = headers

		# TODO handle OSError and 500/502, like dpy does
		async with self.http.request(method, self.BASE_URL + path, **kwargs) as resp:
			if resp.status == HTTPStatus.TOO_MANY_REQUESTS:
				return await self._handle_rl(resp, method, path, guild_id, **kwargs)

			data = await json_or_text(resp)
			if resp.status in range(200, 300):
				return data

			error_cls = self.HTTP_ERROR_CLASSES.get(resp.status, HTTPException)
			raise error_cls(resp, data)

	def _check_rl(self, method, guild_id):
		try:
			rls = self.guild_rls[guild_id]
		except KeyError:
			return

		if not rls.validate():
			del self.guild_rls[guild_id]
			return

		retry_at = getattr(rls, method, None)
		if retry_at:
			raise RateLimitedError(retry_at)

	async def _handle_rl(self, resp, method, path, guild_id, **kwargs):
		retry_after = (await resp.json())['retry_after'] / 1000.0
		retry_at = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=retry_after)

		# cache unconditionally in case request() is called again while we're sleeping
		try:
			rls = self.guild_rls[guild_id]
		except KeyError:
			self.guild_rls[guild_id] = rls = GuildRetryTimes()

		setattr(rls, resp.method, retry_at.timestamp())

		if resp.method not in GuildRetryTimes.__slots__ or retry_after < 10.0:
			await asyncio.sleep(retry_after)
			# woo mutual recursion
			return await self.request(method, path, guild_id, **kwargs)

		# we've been hit with one of those crazy high rate limits, which only occur for specific methods
		raise RateLimitedError(retry_at)

	# optimization methods that let us check the RLs before downloading the user's image
	def check_create(self, guild_id):
		self._check_rl('POST', guild_id)

	def check_delete(self, guild_id):
		self._check_rl('DELETE', guild_id)

	async def create(self, *, guild_id, name, image: bytes, role_ids=(), reason=None):
		return await self.request(
			'POST', f'/guilds/{guild_id}/emojis',
			guild_id,
			json=dict(name=name, image=image_utils.image_to_base64_url(image), roles=role_ids),
			reason=reason,
		)

	async def delete(self, *, guild_id, emote_id, reason=None):
		return await self.request('DELETE', f'/guilds/{guild_id}/emojis/{emote_id}', guild_id, reason=reason)

	async def __aenter__(self):
		self.http = await self.http.__aenter__()
		return self

	async def __aexit__(self, *excinfo):
		return await self.http.__aexit__(*excinfo)

	async def close(self):
		return await self.http.close()
