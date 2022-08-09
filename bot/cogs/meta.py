# © lambda#0987 <lambda@lambda.dance>
# SPDX-License-Identifier: AGPL-3.0-or-later

import contextlib

import discord
from discord.ext import commands


class Meta(commands.Cog):
    # TODO does this need to be configurable?
    INVITE_DURATION_SECONDS = 60 * 60 * 3
    MAX_INVITE_USES = 5

    def __init__(self, bot):
        self.bot = bot
        self.support_channel = None

    @commands.command()
    async def support(self, context):
        """Directs you to the support server."""

        try:
            await context.author.send(f'Official support server invite: {self.bot.config.SUPPORT_LINK}')
        except discord.Forbidden:
            with contextlib.suppress(discord.HTTPException):
                await context.message.add_reaction(self.bot.config.SUCCESS_EMOJI)
            with contextlib.suppress(discord.HTTPException):
                await context.send('Unable to send invite in DMs. Please allow DMs from server members.')
        else:
            try:
                await context.message.add_reaction('📬')
            except discord.HTTPException:
                with contextlib.suppress(discord.HTTPException):
                    await context.send('📬')

    @commands.command(aliases=['inv'])
    async def invite(self, context):
        """Gives you a link to add me to your server."""
        permissions = discord.Permissions()
        permissions.update(**dict.fromkeys((
            'read_messages',
            'send_messages',
            'add_reactions',
            'external_emojis',
            'manage_emojis',
            'embed_links',
            'attach_files',
        ), True))

        await context.send('<%s>' % discord.utils.oauth_url(self.bot.user.id, permissions))


def setup(bot):
    bot.add_cog(Meta(bot))

    if not bot.config.SUPPORT_LINK:
        bot.remove_command('support')
