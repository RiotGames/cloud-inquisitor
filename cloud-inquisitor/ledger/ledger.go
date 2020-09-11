package ledger

import (
	"context"
	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
)

type ActionLedger interface {
	Commit(ctx context.Context, action string, resource cloudinquisitor.PassableResource, actionError error) error
}

func GetActionLedger() AWSActionLedgerEntry {
	return GetAWSActionLedger()
}
