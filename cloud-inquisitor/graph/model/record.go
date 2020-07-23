package model

import (
	"github.com/jinzhu/gorm"
)

type Record struct {
	gorm.Model
	RecordID        string    `json:"RecordID"`
	RecordType      string    `json:"recordType"`
	Alias           bool      `json:"alias"`
	ValueRelation   []Value   `gorm:"many2many:record_values;"`
	ZoneRelation    []Zone    `gorm:"many2many:zone_records;"`
	AccountRelation []Account `gorm:"many2many:account_records;"`
}
