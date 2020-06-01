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

import functools

_emote_type_predicates = {
	'': lambda _: True,  # allow usage as a "consume rest" converter
	'all': lambda _: True,
	'static': lambda e: not e.animated,
	'animated': lambda e: e.animated}

# this is kind of a hack to ensure that the last argument is always converted, even if the default is used.
def emote_type_filter_default(command):
	old_callback = command.callback

	@functools.wraps(old_callback)
	async def callback(self, ctx, *args):
		image_type = args[-1]
		image_type = _emote_type_predicates[image_type]
		return await old_callback(self, ctx, *args[:-1], image_type)

	command.callback = callback
	return command
