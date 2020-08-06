package main

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/spf13/cobra"
)

func init() {
	database.AddCommand(databaseMigrate)
}

var databaseMigrate = &cobra.Command{
	Use:   "migrate",
	Short: "(auto)migrate all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		err := graph.MigrateTables()
		if err != nil {
			panic(err)
		}
	},
}
