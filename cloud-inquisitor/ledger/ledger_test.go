package ledger

import (
	"errors"
	"testing"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
)

func TestAWSActionLedgerEnrich(t *testing.T) {
	passableResource := cloudinquisitor.GetMockedPassableResourceAWSRoute53()
	context := cloudinquisitor.GetMockedLambdaContext()
	err := errors.New("SAMPLE_ERROR")

	ledger := GetAWSActionLedger()
	ledger.enrich(
		context,
		passableResource,
		"SAMPLE_ACTION",
		err,
	)
	//TODO
}

func TestAWSLedgerCommit(t *testing.T) {
	//TODO
}
