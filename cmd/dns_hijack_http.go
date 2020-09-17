package main

import (
	"net/http"
	"time"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database"
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
		db, err := database.NewDBConnection()
		if err != nil {
			panic(err)
		}
		defer db.Close()
		// SetMaxIdleConns sets the maximum number of connections in the idle connection pool.
		db.DB().SetMaxIdleConns(10)

		// SetMaxOpenConns sets the maximum number of open connections to the database.
		db.DB().SetMaxOpenConns(100)

		// SetConnMaxLifetime sets the maximum amount of time a connection may be reused.
		db.DB().SetConnMaxLifetime(time.Hour)
		srv := handler.NewDefaultServer(generated.NewExecutableSchema(generated.Config{Resolvers: &graph.Resolver{
			DB: db,
		}}))

		http.Handle("/", playground.Handler("GraphQL playground", "/query"))
		http.Handle("/query", srv)

		logrus.Printf("connect to http://localhost:%s/ for GraphQL playground", port)
		logrus.Fatal(http.ListenAndServe(":"+port, nil))
	},
}
