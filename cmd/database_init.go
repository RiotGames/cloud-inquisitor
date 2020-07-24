package main

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	"github.com/spf13/cobra"
)

func init() {
	database.AddCommand(databaseInit)
}

var databaseInit = &cobra.Command{
	Use:   "init",
	Short: "initialize all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		err := graph.CreateTables()
		if err != nil {
			panic(err)
		}
	},
}
