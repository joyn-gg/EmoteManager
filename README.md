# Emote Manager

[![Discord Bots](https://discordbots.org/api/widget/status/473370418007244852.svg?noavatar=true)](https://discordbots.org/bot/473370418007244852)

Need to edit your server's custom emotes from your phone? Just add this simple bot, and use its commands to do it for you!

**Note:** both you and the bot will need the "Manage Emojis" permission to edit custom server emotes.

To add the bot to your server, visit https://discordapp.com/oauth2/authorize?client_id=473370418007244852&scope=bot&permissions=1074023488.

## Commands

<p>
	To add an emote:
	<ul>
		<li><code>@Emote Manager add <img class="emote" src="https://cdn.discordapp.com/emojis/407347328606011413.png?v=1&size=32" alt=":thonkang:" title=":thonkang:"></code> (if you already have that emote)
		<li><code>@Emote Manager add rollsafe &lt;https://image.noelshack.com/fichiers/2017/06/1486495269-rollsafe.png&gt;</code>
		<li><code>@Emote Manager add speedtest https://cdn.discordapp.com/emojis/379127000398430219.png</code>
	</ul>
	If you invoke <code>@Emote Manager add</code> with an image upload, the image will be used as the emote image, and the filename will be used as the emote name. To choose a different name, simply run it like<br>
	<code>@Emote Manager add :some_emote:</code> instead.
</p>

<p>
	To add several emotes from a zip or tar archive, run <code>@Emote Manager import</code> with an attached file.
	You can also pass a URL to a zip or tar archive.
</p>

<p>
	<code>@Emote Manager export [animated/static]</code> creates a zip file of all emotes
	suitable for use with the <code>import</code> command.
</p>

<p>
	<code>@Emote Manager list</code> gives you a list of all emotes on this server.
</p>

<p>
	<code>@Emote Manager remove emote</code> will remove :emote:.
</p>

<p>
	<code>@Emote Manager rename old_name new_name</code> will rename :old_name: to :new_name:.
</p>


## License

AGPLv3, see LICENSE.md. © 2018–2020 io mintz <io@mintz.cc>
