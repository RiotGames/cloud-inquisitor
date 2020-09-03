package database

// This file will not be regenerated automatically.
//
// It serves as dependency injection for your app, add any dependencies you require here.

import (
	"errors"
	"strings"
	"os"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database/ledger/model"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database/graph/model"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/secrets/vault"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	
	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/mitchellh/mapstructure"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
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

	if !db.HasTable(&model.Distribution{}) {
		db.CreateTable(&model.Distribution{})
	}

	if !db.HasTable(&model.Origin{}) {
		db.CreateTable(&model.Origin{})
	}
	if !db.HasTable(&model.OriginGroup{}) {
		db.CreateTable(&model.OriginGroup{})
	}

	if !db.HasTable(&model.ActionLedger{}) {
		db.CreateTable(&model.ActionLedger{})
	}
	if !db.HasTable(&model.ConfigLedger{}) {
		db.CreateTable(&model.ConfigLedger{})
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
		&model.Account{},
		&model.Zone{},
		&model.Record{},
		&model.Value{},
		&model.Distribution{},
		&model.Origin{},
		&model.OriginGroup{},
		&model.ActionLedger{},
		&model.ConfigLedger{}
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
		&model.Account{},
		&model.Zone{},
		&model.Record{},
		&model.Value{},
		&model.Distribution{},
		&model.Origin{},
		&model.OriginGroup{},
		&model.ActionLedger{},
		&model.ConfigLedger{}
	).Error

	if err != nil {
		return err
	}

	return nil
}

func ActionLedgerCommit(ctx context.Context, action string, metadata map[string]interface{}, actionError error, StepFunctionExeID string) error {
	db, err := NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	var transaction ActionLedgerItem
	lc, _ := lambdacontext.FromContext(ctx)

	metadata["RequestID"] = ctx.AwsRequestID
	metadata["StepFunctionExeID"] = StepFunctionExeID
	metadata["LambdaFunctionArn"] = ctx.InvokedFunctionArn
	metadata["ActionTime"] = time.UTC()
	metadata["ActionError"] = actionError

	err := Decode(metadata, &transaction)
	if err != nil {
		return err
	}

	err = db.Create(&transaction)
	return err
}

type Resolver struct {
	DB *gorm.DB
}
