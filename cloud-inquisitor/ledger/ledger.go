package ledger

import (
	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
)

type ActionLedgerEntry interface {
	Commit(interface{}, cloudinquisitor.PassableResource, string, error) error
}

func GetActionLedger(platform string) ActionLedgerEntry {
	if platform == "aws" {
		return GetAWSActionLedger()
	} else {
		return GetGenericActionLedger()
	}
}
