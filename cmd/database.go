package main

import (
	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(database)
}

var database = &cobra.Command{
	Use:     "database",
	Aliases: []string{"db"},
	Short:   "interact with the Cloud Inquisitor database",
}
