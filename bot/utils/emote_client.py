# © lambda#0987
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import asyncio
import aiohttp
import datetime
import urllib.parse
from typing import Dict
from http import HTTPStatus
from discord import PartialEmoji
import utils.image as image_utils
from utils.errors import RateLimitedError
from discord import HTTPException, Forbidden, NotFound, DiscordServerError

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

    def __init__(self, bot):
        self.guild_rls: Dict[GuildId, float] = {}
        self.http = aiohttp.ClientSession(headers={
            'User-Agent': bot.config.user_agent + ' ' + bot.http.user_agent,
            'Authorization': 'Bot ' + bot.config.DISCORD_TOKEN,  # TODO: Required bot token under 'Bot' + 'Token'
            'X-Ratelimit-Precision': 'millisecond',
        })

    async def request(self, method, path, guild_id, **kwargs):
        self.check_rl(guild_id)

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

    # optimization method that lets us check the RL before downloading the user's image.
    # also lets us preemptively check the RL before doing a request
    def check_rl(self, guild_id):
        try:
            retry_at = self.guild_rls[guild_id]
        except KeyError:
            return

        now = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        if retry_at < now:
            del self.guild_rls[guild_id]
            return

        raise RateLimitedError(retry_at)

    async def _handle_rl(self, resp, method, path, guild_id, **kwargs):
        retry_after = (await resp.json())['retry_after'] / 1000.0
        retry_at = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=retry_after)

        # cache unconditionally in case request() is called again while we're sleeping
        self.guild_rls[guild_id] = retry_at.timestamp()

        if retry_after < 10.0:
            await asyncio.sleep(retry_after)
            # woo mutual recursion
            return await self.request(method, path, guild_id, **kwargs)

        # we've been hit with one of those crazy high rate limits, which only occur for specific methods
        raise RateLimitedError(retry_at)

    async def create(self, *, guild, name, image: bytes, role_ids=(), reason=None):
        data = await self.request(
            'POST', f'/guilds/{guild.id}/emojis',
            guild.id,
            json=dict(name=name, image=image_utils.image_to_base64_url(image), roles=role_ids),
            reason=reason,
        )
        return PartialEmoji(animated=data.get('animated', False), name=data.get('name'), id=data.get('id'))

    async def __aenter__(self):
        self.http = await self.http.__aenter__()
        return self

    async def __aexit__(self, *excinfo):
        return await self.http.__aexit__(*excinfo)

    async def close(self):
        return await self.http.close()
