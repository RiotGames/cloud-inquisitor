package model

import (
	"github.com/jinzhu/gorm"
)

type Account struct {
	gorm.Model
	AccountID string    `json:"accountID"`
	Zones     []*Zone   `json:"zones"`
	Records   []*Record `json:"records"`
}
