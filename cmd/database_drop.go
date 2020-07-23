package main

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	"github.com/spf13/cobra"
)

func init() {
	database.AddCommand(databaseDrop)
}

var databaseDrop = &cobra.Command{
	Use:   "drop",
	Short: "drop all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		db, err := graph.NewDBConnection()
		if err != nil {
			panic(err)
		}
		defer db.Close()

		err = db.DropTableIfExists(
			&model.Account{},
			&model.Zone{},
			&model.Record{},
			&model.Value{},
			"account_zones",
			"account_records",
			"zone_records",
			"record_values",
		).Error

		if err != nil {
			panic(err)
		}
	},
}
