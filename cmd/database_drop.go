package main

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/spf13/cobra"
)

func init() {
	database.AddCommand(databaseDrop)
}

var databaseDrop = &cobra.Command{
	Use:   "drop",
	Short: "drop all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		err := graph.DropTables()
		if err != nil {
			panic(err)
		}
	},
}
