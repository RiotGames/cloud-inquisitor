package main

import (
	"net/http"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/generated"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

func init() {
	dnsHijack.AddCommand(dnsHijackHTTP)
	dnsHijackHTTP.Flags().StringVarP(&port, "port", "p", "8080", "graphql http port")
}

var (
	port string
)

//from https://gqlgen.com/getting-started/
var dnsHijackHTTP = &cobra.Command{
	Use:   "http",
	Short: "interact with the DNS Hijack graph",
	Run: func(cmd *cobra.Command, args []string) {
		db, err := graph.NewDBConnection()
		if err != nil {
			panic(err)
		}
		defer db.Close()

		srv := handler.NewDefaultServer(generated.NewExecutableSchema(generated.Config{Resolvers: &graph.Resolver{
			DB: db,
		}}))

		http.Handle("/", playground.Handler("GraphQL playground", "/query"))
		http.Handle("/query", srv)

		logrus.Printf("connect to http://localhost:%s/ for GraphQL playground", port)
		logrus.Fatal(http.ListenAndServe(":"+port, nil))
	},
}
