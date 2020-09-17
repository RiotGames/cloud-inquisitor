package ledger

import (
	"errors"
	"reflect"
	"testing"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
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

}
