package main

import (
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

func init() {
	dnsHijack.AddCommand(dnsHijackQuery)
}

var dnsHijackQuery = &cobra.Command{
	Use:     "query",
	Aliases: []string{"q"},
	Short:   "interact with the DNS Hijack graph",
	Run: func(cmd *cobra.Command, args []string) {
		logrus.Println("doing query")
	},
}
