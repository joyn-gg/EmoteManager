from __future__ import annotations

from typing import Optional, List

import discord
from discord.ext import commands

from .config import Config


class TKBot(commands.AutoShardedBot):
    def __init__(
        self,
        intents,
        config: Config,
        activity: discord.Activity,
        shard_count: Optional[int],
        shard_ids: Optional[List[int]],
    ):
        super().__init__(
            command_prefix=config.DEFAULT_PREFIX,
            intents=intents,
            activity=activity,
            chunk_guilds_at_startup=False,
            member_cache_flags=discord.MemberCacheFlags.none(),
            max_messages=None,
            shard_count=shard_count,
            shard_ids=shard_ids,
        )

        self.config = config
