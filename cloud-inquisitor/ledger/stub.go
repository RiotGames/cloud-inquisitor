package ledger

import (
	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
)

type StubActionLedger struct {
}

func (al StubActionLedger) Commit(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) error {
	return nil
}

func GetStubActionLedger() StubActionLedger {
	return StubActionLedger{}
}
