# © lambda#0987 <lambda@lambda.dance>
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import humanize
import datetime
from discord.ext import commands


class MissingManageEmojisPermission(commands.MissingPermissions):
    """The invoker or the bot doesn't have permissions to manage server emojis."""

    def __init__(self):
        super(Exception, self).__init__(
            f'{self.bot.config.FAILURE_EMOJI} '
            "Sorry, you don't have enough permissions to run this command. "
            'You and I both need the Manage Emojis permission.')


class EmoteManagerError(commands.CommandError):
    """Generic error with the bot. This can be used to catch all bot errors."""
    pass


class ImageProcessingTimeoutError(EmoteManagerError, asyncio.TimeoutError):
    pass


class ImageResizeTimeoutError(ImageProcessingTimeoutError):
    """Resizing the image took too long."""
    def __init__(self):
        super().__init__('Error: resizing the image took too long.')


class ImageConversionTimeoutError(ImageProcessingTimeoutError):
    def __init__(self):
        super().__init__('Error: converting the image to a GIF took too long.')


class HTTPException(EmoteManagerError):
    """The server did not respond with an OK status code. This is only for non-Discord HTTP requests."""
    def __init__(self, status):
        super().__init__(f'URL error: server returned error code {status}')


class RateLimitedError(EmoteManagerError):
    def __init__(self, retry_at):
        if isinstance(retry_at, float):
            # it took me about an HOUR to realize i had to pass tz because utcfromtimestamp returns a NAÏVE time obj!
            retry_at = datetime.datetime.fromtimestamp(retry_at, tz=datetime.timezone.utc)
        # humanize.naturaltime is annoying to work with due to timezones so we use this
        delta = humanize.naturaldelta(retry_at, when=datetime.datetime.now(tz=datetime.timezone.utc))
        super().__init__(f'Error: Discord told me to slow down! Please retry this command in {delta}.')


class EmoteNotFoundError(EmoteManagerError):
    """An emote with that name was not found"""
    def __init__(self, name):
        super().__init__(f'An emote called `{name}` does not exist in this server.')


class FileTooBigError(EmoteManagerError):
    def __init__(self, size, limit):
        self.size = size
        self.limit = limit


class InvalidFileError(EmoteManagerError):
    """The file is not a zip, tar, GIF, PNG, JPG, or WEBP file."""
    def __init__(self):
        super().__init__('Invalid file given.')


class InvalidImageError(InvalidFileError):
    """The image is not a GIF, PNG, or JPG"""
    def __init__(self):
        super(Exception, self).__init__('The image supplied was not a GIF, PNG, JPG, or WEBP file.')


class PermissionDeniedError(EmoteManagerError):
    """Raised when a user tries to modify an emote without the Manage Emojis permission"""
    def __init__(self, name):
        super().__init__(f"You're not authorized to modify `{name}`.")


class DiscordError(Exception):
    """Usually raised when the client cache is being baka"""
    def __init__(self):
        super().__init__('Discord seems to be having issues right now, please try again later.')
