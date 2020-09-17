package main

import (
	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(cmdDatabase)
}

var cmdDatabase = &cobra.Command{
	Use:     "database",
	Aliases: []string{"db"},
	Short:   "interact with the Cloud Inquisitor database",
}
