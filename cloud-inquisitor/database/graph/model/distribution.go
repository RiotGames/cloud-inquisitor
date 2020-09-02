package model

import "github.com/jinzhu/gorm"

type Distribution struct {
	gorm.Model
	DistributionID string   `json:"distributionID"`
	Domain         string   `json:"domain"`
	OriginRelation []Origin `json:"origins"`
	AccountID      uint
}
