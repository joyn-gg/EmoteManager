# Emote Manager

Emote Manager is a souped up version of the Emoji settings screen in your server's settings.

**Note:** both you and the bot will need the "Manage Emojis" permission to edit custom server emotes.

## Commands

<p>
	To add an emote:
	<ul>
		<li><u>em/add <img class="emote" src="https://cdn.discordapp.com/emojis/407347328606011413.png?v=1&size=32" alt=":thonkang:" title=":thonkang:"></u> (if you already have that emote)
		<li><u>em/add rollsafe &lt;https://image.noelshack.com/fichiers/2017/06/1486495269-rollsafe.png&gt;</u>
		<li><u>em/add speedtest https://cdn.discordapp.com/emojis/379127000398430219.png</u>
	</ul>
	If you invoke <u>em/add</u> with an image upload, the image will be used as the emote image, and the filename will be used as the emote name. To choose a different name, simply run it like<br>
	<u>em/add your_emote_name_here</u> instead.
</p>

<p>
	To add a bunch of custom emotes, use <u>em/add-these [emote 1] [emote 2] [emote 3]&hellip;</u>.
</p>

<p>
    To add several emotes from a zip or tar archive, run <u>em/import</u> with an attached file.
    You can also pass a URL to a zip or tar archive.
</p>

<p>
    <u>em/export [animated/static/all]</u> creates a zip file of all emotes
    suitable for use with the <u>import</u> command.
</p>

<p>
	<u>em/list [animated/static/all]</u> gives you a list of all emotes on this server.
</p>

<p>
	<u>em/remove emote</u> will remove :emote:.
</p>

<p>
	<u>em/rename old_name new_name</u> will rename :old_name: to :new_name:.
</p>

## Automatic GIF conversion

If you try to upload a static emote to a server that has no more static slots, the bot will automatically convert the image to a GIF.
When this happens, the bot will let you know.
