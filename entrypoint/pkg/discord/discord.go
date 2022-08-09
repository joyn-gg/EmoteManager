//-- Package Declaration -------------------------------------------------------------------------------------------------------

package discord

//-- Imports -------------------------------------------------------------------------------------------------------------------
import (
	"fmt"
	"log"
	"strings"

	"github.com/bwmarrin/discordgo"
)

//-- Types ---------------------------------------------------------------------------------------------------------------------

type ShardGroup struct {
	ID          int
	Environment []string
}

//-- Shared Variables ----------------------------------------------------------------------------------------------------------
const (
	defaultShardsPerProcess = 3

	environmentShardIDsName   = `DISCORD_SHARD_IDS`
	environmentShardCountName = `DISCORD_SHARD_COUNT`
)

//-- Exported Functions --------------------------------------------------------------------------------------------------------

func GetDiscordShardEnvironments(shardsPerProcess *int, shardIDs []int, botToken string) ([]*ShardGroup, error) {
	//-- Determine shards per process (defaulted to stated constant) ----------
	if shardsPerProcess == nil || *shardsPerProcess < 1 {
		*shardsPerProcess = defaultShardsPerProcess
	}

	//-- Determine shard count (as stated by Discord) ----------
	var discordShardTotal int
	{
		if client, err := discordgo.New(fmt.Sprintf(`Bot %s`, botToken)); err != nil {
			return nil, fmt.Errorf(`unexpected error while trying to connect to discord: %s`, err.Error())
		} else if result, err := client.GatewayBot(); err != nil {
			return nil, fmt.Errorf(`unexpected error while querying discord's shard recommendations': %s`, err.Error())
		} else if result.Shards <= 0 {
			return nil, fmt.Errorf(`invalid shard count returned from discord query: %d`, result.Shards)
		} else {
			discordShardTotal = result.Shards
		}
	}

	//-- Determine shard ids to be split between processes (from consumer or as extrapolated from Discord results) ----------
	if len(shardIDs) == 0 {
		log.Printf(`no explicit shard IDs provided, falling back to discord for shard definition...`)
		for id := 0; id < discordShardTotal; id = id + 1 {
			shardIDs = append(shardIDs, id)
		}
	}

	//-- Create shard groups environments ----------
	var groups []*ShardGroup
	{
		log.Printf(`%d shards required, parsing into %d shardGroups`, len(shardIDs), len(shardIDs) / *shardsPerProcess)
		var requiredShardGroups = len(shardIDs) / *shardsPerProcess
		if len(shardIDs)%*shardsPerProcess != 0 {
			requiredShardGroups = requiredShardGroups + 1
		}

		for groupID := 0; groupID < requiredShardGroups; groupID = groupID + 1 {
			var group = ShardGroup{
				ID:          groupID,
				Environment: nil,
			}

			var groupShardIDs []string
			for offset := 0; offset < *shardsPerProcess; offset = offset + 1 {
				var index = (groupID * *shardsPerProcess) + offset
				if index < len(shardIDs) {
					groupShardIDs = append(groupShardIDs, fmt.Sprintf(`%d`, shardIDs[index]))
				}
			}

			group.Environment = append(group.Environment, fmt.Sprintf(`%s=[%s]`, environmentShardIDsName, strings.Join(groupShardIDs, `,`)))
			group.Environment = append(group.Environment, fmt.Sprintf(`%s=%d`, environmentShardCountName, discordShardTotal))
			log.Printf(`group %d will run with environment modifiers: %s`, groupID, strings.Join(group.Environment, ` && `))

			groups = append(groups, &group)
		}
	}

	return groups, nil
}

//-- Internal Functions --------------------------------------------------------------------------------------------------------
