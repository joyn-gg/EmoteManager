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

_emote_type_predicates = {
	'': lambda _: True,  # allow usage as a "consume rest" converter
	'all': lambda _: True,
	'static': lambda e: not e.animated,
	'animated': lambda e: e.animated}

def emote_type_filter(argument):
	try:
		return _emote_type_predicates[argument.lower()]
	except KeyError:
		raise commands.BadArgument('Invalid emote type. Specify “static”, “animated”, “all”.')
