package model

import (
	"github.com/jinzhu/gorm"
)

type S3 struct {
	gorm.Model
	AccountID uint
	S3ID      string `json:"s3ID"`
	CName     string `json:"cname"`
	Region    string `json:"region"`
}
