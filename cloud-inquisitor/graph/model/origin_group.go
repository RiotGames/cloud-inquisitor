package model

import "github.com/jinzhu/gorm"

type OriginGroup struct {
	gorm.Model
	GroupID        string  `json:"groupID"`
	Origins        []Value `json:"origins"`
	DistributionID uint
}
