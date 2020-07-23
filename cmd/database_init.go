package main

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	"github.com/spf13/cobra"
)

func init() {
	database.AddCommand(databaseInit)
}

var databaseInit = &cobra.Command{
	Use:   "init",
	Short: "initialize all tables in the Cloud Inquisitor database",
	Run: func(cmd *cobra.Command, args []string) {
		db, err := graph.NewDBConnection()
		if err != nil {
			panic(err)
		}
		defer db.Close()

		if !db.HasTable(&model.Account{}) {
			db.CreateTable(&model.Account{})
		}
		if !db.HasTable(&model.Zone{}) {
			db.CreateTable(&model.Zone{})
		}
		if !db.HasTable(&model.Record{}) {
			db.CreateTable(&model.Record{})
		}
		if !db.HasTable(&model.Value{}) {
			db.CreateTable(&model.Value{})
		}

		if err != nil {
			panic(err)
		}
	},
}
