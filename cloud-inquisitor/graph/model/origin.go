package model

import "github.com/jinzhu/gorm"

type Origin struct {
	gorm.Model
	OriginID       string  `json:"originID"`
	Domains        []Value `json:"values"`
	DistributionID uint
}
