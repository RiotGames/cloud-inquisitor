package model

import "github.com/jinzhu/gorm"

type ElasticbeanstalkEnvironment struct {
	gorm.Model
	AccountID       uint
	EnvironmentID   string `json:"environmentID"`
	ApplicationName string `json:"applicationName"`
	EnvironmentName string `json:"environmentName"`
	EnvironmentURL  string `json:"environmentURL"`
	CName           string `json:"cname"`
	Region          string `json:"region"`
}
