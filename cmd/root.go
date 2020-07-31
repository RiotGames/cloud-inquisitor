package main

import (
	"os"

	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "cinqctl",
	Short: "cinqctl is a cli tool for interacting with Cloud Inquisitor",
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		logrus.Println(err)
		os.Exit(1)
	}
}
