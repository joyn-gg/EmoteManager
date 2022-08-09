//-- Package Declaration -------------------------------------------------------------------------------------------------------
package configuration

//-- Imports -------------------------------------------------------------------------------------------------------------------
import (
	"bytes"
	"encoding/json"
	"log"

	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
)

//-- Types ---------------------------------------------------------------------------------------------------------------------
type configuration struct {
	DiscordToken            *string `yaml:"discord_token" mapstructure:"discord_token"`
	DiscordShardIDs         *string `yaml:"discord_shard_ids" mapstructure:"discord_shard_ids"`
	DiscordShardsPerProcess *int    `yaml:"discord_shards_per_process" mapstructure:"discord_shards_per_process"`
}

//-- Shared Variables ----------------------------------------------------------------------------------------------------------
var config *configuration

//-- Exported Functions --------------------------------------------------------------------------------------------------------
func Configuration() *configuration {
	if config == nil {
		var newConfig = new(configuration)

		if binder, err := yaml.Marshal(newConfig); err != nil {
			log.Fatalf(`unable to marshal configuration binding to yaml: %v`, err)
		} else {
			viper.SetConfigType(`yaml`)
			if err := viper.ReadConfig(bytes.NewBuffer(binder)); err != nil {
				log.Fatalf(`unable to read configuration yaml binding into viper: %v`, err)
			}
			viper.AutomaticEnv()
		}

		if err := viper.Unmarshal(newConfig); err != nil {
			log.Fatalf(`unable to parse configuration: %v`, err)
			return nil
		} else {
			config = newConfig
		}
	}

	return config
}

func (c configuration) ParsedShardIDs() []int {
	var parsedIDs []int
	if c.DiscordShardIDs == nil {
		return nil
	} else if err := json.Unmarshal([]byte(*c.DiscordShardIDs), &parsedIDs); err != nil {
		return nil
	}

	return parsedIDs
}

//-- Internal Functions --------------------------------------------------------------------------------------------------------
