# © lambda#0987 <lambda@lambda.dance>
# SPDX-License-Identifier: AGPL-3.0-or-later

from .misc import (
    format_user,
    format_http_exception,
    strip_angle_brackets,
    gather_or_cancel,
)
from . import archive
from . import emote
from . import errors
from . import paginator

__all__ = (
    archive,
    emote,
    errors,
    paginator,
    format_user,
    format_http_exception,
    strip_angle_brackets,
    gather_or_cancel,
)
# note: do not import .image in case the user doesn't want it
# since importing image can take a long time.
# Do not import .emote_client, either, because otherwise running python -m utils.image
# will cause utils.image to appear in sys.modules after import of package 'utils' but
# prior to execution of 'utils.image' which may result in unpredictable behavior.
