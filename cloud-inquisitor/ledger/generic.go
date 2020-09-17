package ledger

import (
	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
)

type GenericActionLedger struct {
}

func (al GenericActionLedger) Commit(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) error {
	return nil
}

func GetGenericActionLedger() GenericActionLedger {
	return GenericActionLedger{}
}
