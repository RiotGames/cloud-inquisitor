package model

import (
	"github.com/jinzhu/gorm"
)

type Record struct {
	gorm.Model
	RecordID      string `json:"RecordID"`
	RecordType    string `json:"recordType"`
	Alias         bool   `json:"alias"`
	ValueRelation []Value
	ZoneID        uint
	AccountID     uint
}
