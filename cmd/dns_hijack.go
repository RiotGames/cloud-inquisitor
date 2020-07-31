package main

import (
	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(dnsHijack)
}

var dnsHijack = &cobra.Command{
	Use:     "dns-hijack",
	Aliases: []string{"dns"},
	Short:   "interact with the DNS Hijack processes",
}
