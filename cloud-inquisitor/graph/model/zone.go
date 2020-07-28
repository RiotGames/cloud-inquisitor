package model

import (
	"github.com/jinzhu/gorm"
)

type Zone struct {
	gorm.Model
	ZoneID         string `json:"zoneID"`
	Name           string `json:"name"`
	ServiceType    string `json:"serviceType"`
	RecordRelation []Record
	AccountID      uint
}
