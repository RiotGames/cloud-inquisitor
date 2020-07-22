package model

import (
	"github.com/jinzhu/gorm"
)

type Zone struct {
	gorm.Model
	ZoneID      string `json:"zoneID"`
	AccountID   uint
	Name        string    `json:"name"`
	ServiceType string    `json:"serviceType"`
	Records     []*Record `json:"records"`
}
