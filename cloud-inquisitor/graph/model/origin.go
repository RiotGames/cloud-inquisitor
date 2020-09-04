package model

import "github.com/jinzhu/gorm"

type Origin struct {
	gorm.Model
	OriginID       string `json:"originID"`
	Domain         string `json:"domain"`
	DistributionID uint
}
