package main

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database"
	graphmodel "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	ledgermodel "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/ledger"
)

func CreateTables() error {
	db, err := database.NewDBConnection()
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

	if !db.HasTable(&ledgermodel.AWSActionLedgerEntry{}) {
		db.CreateTable(&ledgermodel.AWSActionLedgerEntry{})
	}

	return nil
}

func DropTables() error {
	db, err := database.NewDBConnection()
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
		&ledgermodel.AWSActionLedgerEntry{},
	).Error

	if err != nil {
		return err
	}

	return nil
}

func MigrateTables() error {
	db, err := database.NewDBConnection()
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
		&ledgermodel.AWSActionLedgerEntry{},
	).Error

	if err != nil {
		return err
	}

	return nil
}
