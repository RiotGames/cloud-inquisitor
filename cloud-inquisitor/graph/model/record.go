package model

import (
	"github.com/jinzhu/gorm"
)

type Record struct {
	gorm.Model
	RecordID   string   `json:"RecordID"`
	RecordType string   `json:"recordType"`
	Values     []*Value `json:"values"`
	Alias      bool     `json:"alias"`
	AccountID  uint
}
