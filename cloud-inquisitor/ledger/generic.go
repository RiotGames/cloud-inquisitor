package ledger

import (
	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/jinzhu/gorm"
)

type GenericActionLedgerEntry struct {
	gorm.Model
}

func (al GenericActionLedgerEntry) Commit(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) error {
	return nil
}

func GetGenericActionLedger() GenericActionLedgerEntry {
	return GenericActionLedgerEntry{}
}
