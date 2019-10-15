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
