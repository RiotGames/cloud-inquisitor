package model

import (
	"github.com/jinzhu/gorm"
)

type Account struct {
	gorm.Model
	AccountID            string `json:"accountID"`
	ZoneRelation         []Zone
	RecordRelation       []Record
	DistributionRelation []Distribution
}
