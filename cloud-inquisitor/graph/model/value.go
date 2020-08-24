package model

import (
	"github.com/jinzhu/gorm"
)

type Value struct {
	gorm.Model
	ValueID  string `json:"valueID"`
	RecordID uint
	OriginID uint
}
