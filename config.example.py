{
	'description':
		'Emote Manager lets you manage custom server emotes from your phone.\n\n'
		'NOTE: Most commands will be unavailable until both you and the bot have the '
		'"Manage Emojis" permission.',

	# a channel ID to invite people to when they request help with the bot
	# the bot must have Create Instant Invite permissions for this channel
	# if set to None, the support command will be disabled
	'support_server_invite_channel': None,

	'tokens': {
		'discord': 'sek.rit.token',
		'stats': {
			'bots.discord.pw': None,
			'discordbots.org': None,
			'botsfordiscord.com': None,
		},
	},

	'ignore_bots': {
		'default': True,
		'overrides': {
			'channels': [
			],
			'guilds': [
			],
		},
	},

	'copyright_license_file': 'short-license.txt',

	'socks5_proxy_url': None,  # required for connecting to the EC API over a Tor onion service
	'use_socks5_for_all_connections': False,  # whether to use socks5 for all HTTP operations (other than discord.py)
	'user_agent': 'EmoteManagerBot (https://github.com/iomintz/emote-manager-bot)',
	'ec_api_base_url': None,  # set to None to use the default of https://ec.emote.bot/api/v0
	'http_head_timeout': 10,  # timeout for the initial HEAD request before retrieving any images (up this if using Tor)
	'http_read_timeout': 60,  # timeout for retrieving an image

	# emotes that the bot may use to respond to you
	# If not provided, the bot will use '❌', '✅' instead.
	#
	# You can obtain these ones from the discordbots.org server under the name "tickNo" and "tickYes"
	# but I uploaded them to my test server
	# so that both the staging and the stable versions of the bot can use them
	'response_emojis': {
		'success': {  # emotes used to indicate success or failure
			False: '<:error:478164511879069707>',
			True: '<:success:478164452261363712>'
		},
	},
}
