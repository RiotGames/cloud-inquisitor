package main

import (
	"github.com/spf13/cobra"
)

func init() {
	cmdDatabase.AddCommand(databaseMigrate)
}

var databaseMigrate = &cobra.Command{
	Use:   "migrate",
	Short: "(auto)migrate all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		err := MigrateTables()
		if err != nil {
			panic(err)
		}
	},
}
