{
	'description':
		'Emote Manager lets you manage custom server emotes from your phone.\n\n'
		'NOTE: Most commands will be unavailable until both you and the bot have the '
		'"Manage Emojis" permission.',

	'support_server_invite': 'https://discord.gg/some-invite',

	'cogs': (
		'cogs.emote',
		'cogs.meta',
		'ben_cogs.debug',
		'ben_cogs.misc',
		'ben_cogs.debug'
		'jishaku',
	),

	'tokens': {
		'discord': 'sek.rit.token',
		'stats': {
			'bots.discord.pw': None,
			'discordbots.org': None,
			'botsfordiscord.com': None,
		},
	},

	'user_agent': 'EmojiManagerBot (https://github.com/bmintz/emoji-manager-bot)',

	'ec_api_url': 'https://emoji-connoisseur.python-for.life/api/v0',

	# emotes that the bot may use to respond to you
	# If not provided, the bot will use ('❌', '✅') instead.
	#
	# You can obtain these ones from the discordbots.org server under the name "tickNo" and "tickYes"
	# but I uploaded them to my test server
	# so that both the staging and the stable versions of the bot can use them
	'response_emotes': {
		'success': {  # emotes used to indicate success or failure
			False: '<:error:478164511879069707>',
			True: '<:success:478164452261363712>'
		},
	},
}
