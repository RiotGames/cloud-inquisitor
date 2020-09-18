package ledger

import (
	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
)

type ActionLedgerEntry interface {
	Commit(interface{}, cloudinquisitor.PassableResource, string, error) error
}

func GetActionLedger(platform string) ActionLedgerEntry {
	switch platform {
	case "aws":
		return GetAWSActionLedger()
	default:
		return GetStubActionLedger()
	}
}
