# © lambda#0987 <lambda@lambda.dance>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""various utilities for use within the bot"""

import asyncio

import discord


def format_user(user, *, mention=False):
    """Format a user object for audit log purposes."""
    # not mention: @null byte#8191 (140516693242937345)
    # mention: <@140516693242937345> (null byte#8191)
    # this allows people to still see the username and discrim
    # if they don't share a server with that user
    if mention:
        return f'{user.mention} (@{user})'
    else:
        return f'@{user} ({user.id})'


def format_http_exception(exception: discord.HTTPException):
    """Formats a discord.HTTPException for relaying to the user.

    Sample return value:
    BAD REQUEST (status code: 400):
    Invalid Form Body
    In image: File cannot be larger than 256 kb.
    """
    return (
        f'{exception.response.reason} (status code: {exception.response.status}):'
        f'\n{exception.text}')


def strip_angle_brackets(string):
    """Strip leading < and trailing > from a string.
    Useful if a user sends you a url like <this> to avoid embeds, or to convert emotes to reactions."""
    if string.startswith('<') and string.endswith('>'):
        return string[1:-1]
    return string


async def gather_or_cancel(*awaitables, loop=None):
    """
    run the awaitables in the sequence concurrently. If any of them raise an exception,
    propagate the first exception raised and cancel all other awaitables.
    """
    gather_task = asyncio.gather(*awaitables, loop=loop)
    try:
        return await gather_task
    except asyncio.CancelledError:
        raise
    except Exception:
        gather_task.cancel()
        raise
