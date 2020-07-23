package model

import (
	"github.com/jinzhu/gorm"
)

type Account struct {
	gorm.Model
	AccountID      string   `json:"accountID"`
	ZoneRelation   []Zone   `gorm:"many2many:account_zones;"`
	RecordRelation []Record `gorm:"many2many:account_records;"`
}
