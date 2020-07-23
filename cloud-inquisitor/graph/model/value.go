package model

import (
	"github.com/jinzhu/gorm"
)

type Value struct {
	gorm.Model
	ValueID        string   `json:"valueID"`
	RecordRelation []Record `gorm:"many2many:record_values;"`
}
