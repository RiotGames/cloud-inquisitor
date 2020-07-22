package graph

// This file will not be regenerated automatically.
//
// It serves as dependency injection for your app, add any dependencies you require here.

import (
	"errors"
	"strings"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/secrets/vault"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
)

var intialized bool = false

func init() {
	//do all database related setup
	db, err := NewDBConnection()
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
}

func NewDBConnection() (*gorm.DB, error) {
	if settings.IsSet("mysql") {
		var connectionString string
		var err error = nil
		switch settings.GetString("mysql.connection_string.type") {
		case "vault":
			connectionString, err = vault.GetString(settings.GetString("mysql.connection_string.value"), "value")
			if err != nil {
				return nil, err
			}
		case "string":
			connectionString = settings.GetString("mysql.connection_string.value")
		default:
			return nil, errors.New("unknown datastore/graph configuration type")
		}

		if connectionString == "" {
			return nil, errors.New("datastore/graph connection is empty")
		}

		if !strings.HasSuffix(connectionString, "?parseTime=true") {
			connectionString = connectionString + "?parseTime=true"
		}

		return gorm.Open("mysql", connectionString)
	}

	return nil, errors.New("no mysql connection config provided")
}

type Resolver struct {
	DB *gorm.DB
}
