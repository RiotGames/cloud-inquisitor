package ledger

import (
	"context"
	"time"

	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/jinzhu/gorm"
	"github.com/mitchellh/mapstructure"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/cloud-inquisitor/database"
)

type AWSActionLedger struct {
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

func (al *AWSActionLedger) Commit(ctx context.Context, action string, metadata map[string]interface{}, actionError error) error {
	db, err := database.NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	var transaction AWSActionLedgerItem
	tz, _ := time.LoadLocation("UTC")
	lc, _ := lambdacontext.FromContext(ctx)

	metadata["RequestID"] = lc.AwsRequestID
	metadata["LambdaFunctionArn"] = lc.InvokedFunctionArn
	metadata["ActionTime"] = time.Now().In(tz)
	metadata["ActionError"] = actionError

	err := mapstructure.Decode(metadata, &transaction)
	if err != nil {
		return err
	}

	err = db.Create(&transaction)
	return err
}

func GetAWSActionLedger() AWSActionLedger {
	return AWSActionLedger{}
}
