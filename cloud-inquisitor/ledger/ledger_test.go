package ledger

import (
	"errors"
	"reflect"
	"testing"

	"github.com/google/uuid"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database"
)

func TestAWSActionLedgerGenerate(t *testing.T) {
	passableResource := cloudinquisitor.GetMockedPassableResourceAWSRoute53()
	context := cloudinquisitor.GetMockedLambdaContext()
	err := errors.New("SAMPLE_ERROR")

	ledger := GetAWSActionLedger()
	ledgerEntry, err := ledger.generateEntry(
		context,
		passableResource,
		"SAMPLE_ACTION",
		err,
	)
	if err != nil {
		t.Fatal("Failed to generate ledger entry!")
	}

	r := reflect.ValueOf(ledgerEntry)
	tp := r.Type()

	for i := 0; i < r.NumField(); i++ {
		propertyName := tp.Field(i).Name
		propertyValue := r.Field(i).Interface()
		if val, ok := passableResource.Metadata[propertyName]; ok {
			if val != propertyValue {
				t.Fatal("Generated entry does not match given metadata")
			}
		}
	}
}

func TestAWSLedgerCommit(t *testing.T) {
	passableResource := cloudinquisitor.GetMockedPassableResourceAWSRoute53()
	context := cloudinquisitor.GetMockedLambdaContext()
	uid := uuid.New().String()
	err := errors.New(uid)

	ledger := GetAWSActionLedger()
	err = ledger.Commit(
		context,
		passableResource,
		"SAMPLE_ACTION",
		err,
	)
	if err != nil {
		t.Fatal("Failed to commit ledger entry!")
	}

	db, err := database.NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		t.Fatal("Failed to establish DB connection!")
	}
	defer db.Close()

	var entryFromDB AWSActionLedgerEntry
	result := db.Where("action_error = ?", uid).First(&entryFromDB)
	if result.RowsAffected <= 0 {
		t.Fatal("Ledger entry retrieved from DB does not match the origin entry!")
	}
}
