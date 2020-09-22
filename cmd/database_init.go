package main

import (
	"github.com/spf13/cobra"
)

func init() {
	cmdDatabase.AddCommand(databaseInit)
}

var databaseInit = &cobra.Command{
	Use:   "init",
	Short: "initialize all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		err := CreateTables()
		if err != nil {
			panic(err)
		}
	},
}
