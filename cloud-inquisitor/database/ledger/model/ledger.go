package model

import (
	"time"

	"github.com/jinzhu/gorm"
)

type ActionLedgerItem struct {
	gorm.Model

	RequestID          string    `json:"RequestID"`
	StepFunctionExeID  string    `json:"StepFunctionID"`
	LambdaFunctionName string    `json:"LambdaFunctionName"`
	ActionError        string    `json:"ActionError"`
	AccountID          string    `json:"AccountID" mapstructure:"AccountID"`
	Region             string    `json:"Region" mapstructure:"Region"`
	ActionName         string    `json:"ActionName" mapstructure:"ActionName"`
	ActionTime         time.Time `json:"ActionTime"`
	ResourceID         string    `json:"ResourceID" mapstructure:"ResourceID"`
	ResourceAltID      string    `json:"ResourceAltID" mapstructure:"ResourceAltID"`
	ResourceName       string    `json:"ResourceName" mapstructure:"ResourceName"`
	ResourceType       string    `json:"ResourceType" mapstructure:"ResourceType"`
	ResourceSubType    string    `json:"ResourceSubType" mapstructure:"ResourceSubType"`
}

type ConfigLedgerItem struct {
	gorm.Model

	ConfigurationPath string `json:"ConfigurationPath"`
	Action            string `json:"Action"`
	PreviousVaule     string `json:"PreviousVaule"`
	CurrentValue      string `json:"CurrentValue"`
	User              string `json:"User"`
}
