package main

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/tidwall/pretty"
)

func init() {
	dnsHijack.AddCommand(dnsHijackQuery)
	dnsHijackQuery.Flags().StringVarP(&queryFile, "file", "f", "", "graphql query to run")
}

var (
	queryFile string
)

var dnsHijackQuery = &cobra.Command{
	Use:     "query",
	Aliases: []string{"q"},
	Short:   "interact with the DNS Hijack graph",
	Run: func(cmd *cobra.Command, args []string) {
		logrus.Println("doing query")
		if queryFile != "" {
			absQueryFile, err := filepath.Abs(queryFile)
			if err != nil {
				logrus.Panic(err.Error())
			}

			fileReader, err := os.Open(absQueryFile)
			if err != nil {
				logrus.Panic(err.Error())
			}

			query, err := graph.ParseGraphqlQuery(fileReader)
			if err != nil {
				logrus.Panic(err.Error())
			}

			logrus.Printf("query: %#v\n", *query)

			graphHandler, err := graph.NewGraph()
			if err != nil {
				logrus.Panic(err.Error())
			}

			data, err := graphHandler.ExecuteGraphqlQuery(query)
			if err != nil {
				logrus.Panic(err.Error())
			}

			result, err := json.Marshal(&data)
			if err != nil {
				logrus.Panic(err.Error())
			}

			logrus.Println("\n" + string(pretty.Pretty(result)))
		}
	},
}
