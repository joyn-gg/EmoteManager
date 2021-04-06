SET TIME ZONE 'UTC';

-- inserted for every time a command is invoked
CREATE TABLE invokes (
	guild_id BIGINT NOT NULL,
	-- hashed for privacy
	user_id_md5 BYTEA NOT NULL,
	-- the qualified name of the command invoked (https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=qualified_name#discord.ext.commands.Command.qualified_name)
	command TEXT NOT NULL,
	invoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX invokes_invoked_at_idx ON invokes (invoked_at);

CREATE TABLE shard_member_counts (
	shard_id INT2 PRIMARY KEY,
	-- sum(guild.member_count for guild in shard)
	member_count INT4 NOT NULL
);