package model

import (
	"context"
	"time"

	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/jinzhu/gorm"
)

type AWSActionLedgerItem struct {
	gorm.Model

	RequestID          string    `json:"RequestID"`
	StepFunctionExeID  string    `json:"StepFunctionExeID" mapstructure:"StepFunctionExeID"`
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

type AWSConfigLedgerItem struct {
	gorm.Model

	ConfigurationPath string `json:"ConfigurationPath"`
	Action            string `json:"Action"`
	PreviousVaule     string `json:"PreviousVaule"`
	CurrentValue      string `json:"CurrentValue"`
	User              string `json:"User"`
}

func (al *AWSActionLedgerItem) Commit(ctx context.Context, action string, metadata map[string]interface{}, actionError error) error {
	db, err := NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	var transaction ActionLedgerItem
	lc, _ := lambdacontext.FromContext(ctx)

	metadata["RequestID"] = ctx.AwsRequestID
	metadata["LambdaFunctionArn"] = ctx.InvokedFunctionArn
	metadata["ActionTime"] = time.UTC()
	metadata["ActionError"] = actionError

	err := Decode(metadata, &transaction)
	if err != nil {
		return err
	}

	err = db.Create(&transaction)
	return err
}
