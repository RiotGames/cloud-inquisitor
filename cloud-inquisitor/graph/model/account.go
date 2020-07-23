package model

import (
	"github.com/jinzhu/gorm"
)

type Account struct {
	gorm.Model
	AccountID      string `json:"accountID"`
	ZoneRelation   []Zone
	RecordRelation []Record
}

func (a *Account) ZoneIDs() []string {
	return []string{}
}

func (a *Account) RecordIDs() []string {
	return []string{}
}
