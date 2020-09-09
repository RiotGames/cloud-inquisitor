package database

import (
	"errors"
	graphmodel "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	ledgermodel "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/ledger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/secrets/vault"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	"strings"
)

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

func CreateTables() error {
	db, err := NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	if !db.HasTable(&graphmodel.Account{}) {
		db.CreateTable(&graphmodel.Account{})
	}
	if !db.HasTable(&graphmodel.Zone{}) {
		db.CreateTable(&graphmodel.Zone{})
	}
	if !db.HasTable(&graphmodel.Record{}) {
		db.CreateTable(&graphmodel.Record{})
	}
	if !db.HasTable(&graphmodel.Value{}) {
		db.CreateTable(&graphmodel.Value{})
	}

	if !db.HasTable(&graphmodel.Distribution{}) {
		db.CreateTable(&graphmodel.Distribution{})
	}

	if !db.HasTable(&graphmodel.Origin{}) {
		db.CreateTable(&graphmodel.Origin{})
	}
	if !db.HasTable(&graphmodel.OriginGroup{}) {
		db.CreateTable(&graphmodel.OriginGroup{})
	}

	if !db.HasTable(&ledgermodel.AWSActionLedger{}) {
		db.CreateTable(&ledgermodel.AWSActionLedger{})
	}

	return nil
}

func DropTables() error {
	db, err := NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	err = db.DropTableIfExists(
		&graphmodel.Account{},
		&graphmodel.Zone{},
		&graphmodel.Record{},
		&graphmodel.Value{},
		&graphmodel.Distribution{},
		&graphmodel.Origin{},
		&graphmodel.OriginGroup{},
		&ledgermodel.AWSActionLedger{},
	).Error

	if err != nil {
		return err
	}

	return nil
}

func MigrateTables() error {
	db, err := NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	err = db.AutoMigrate(
		&graphmodel.Account{},
		&graphmodel.Zone{},
		&graphmodel.Record{},
		&graphmodel.Value{},
		&graphmodel.Distribution{},
		&graphmodel.Origin{},
		&graphmodel.OriginGroup{},
		&ledgermodel.AWSActionLedger{},
	).Error

	if err != nil {
		return err
	}

	return nil
}
