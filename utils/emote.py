# © lambda#0987 <lambda@lambda.dance>
# SPDX-License-Identifier: AGPL-3.0-or-later

import re

"""
various utilities related to custom emotes
"""

"""Matches :foo: and ;foo; but not :foo;. Used for emotes in text."""
RE_EMOTE = re.compile(r'(:|;)(?P<name>\w{2,32})\1|(?P<newline>\n)', re.ASCII)

"""Matches only custom server emotes."""
RE_CUSTOM_EMOTE = re.compile(r'<(?P<animated>a?):(?P<name>\w{2,32}):(?P<id>\d{17,})>', re.ASCII)

def url(id, *, animated: bool = False):
	"""Convert an emote ID to the image URL for that emote."""
	extension = 'gif' if animated else 'png'
	return f'https://cdn.discordapp.com/emojis/{id}.{extension}?v=1'
