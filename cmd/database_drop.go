package main

import (
	"github.com/spf13/cobra"
)

func init() {
	cmdDatabase.AddCommand(databaseDrop)
}

var databaseDrop = &cobra.Command{
	Use:   "drop",
	Short: "drop all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		err := DropTables()
		if err != nil {
			panic(err)
		}
	},
}
