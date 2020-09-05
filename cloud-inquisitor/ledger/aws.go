package ledger

import (
	"context"
	"time"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/cloud-inquisitor/database"
	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/jinzhu/gorm"
	"github.com/mitchellh/mapstructure"
)

type AWSActionLedger struct {
	gorm.Model

	RequestID               string    `json:"RequestID"`
	StepFunctionExecutionID string    `json:"StepFunctionExecutionID"`
	LambdaFunctionArn       string    `json:"LambdaFunctionArn"`
	ActionError             string    `json:"ActionError"`
	AccountID               string    `json:"AccountID" mapstructure:"AccountID"`
	Region                  string    `json:"Region" mapstructure:"Region"`
	ActionName              string    `json:"ActionName" mapstructure:"ActionName"`
	ActionTime              time.Time `json:"ActionTime"`
	ResourceID              string    `json:"ResourceID" mapstructure:"ResourceID"`
	ResourceAltID           string    `json:"ResourceAltID" mapstructure:"ResourceAltID"`
	ResourceName            string    `json:"ResourceName" mapstructure:"ResourceName"`
	ResourceType            string    `json:"ResourceType" mapstructure:"ResourceType"`
	ResourceSubType         string    `json:"ResourceSubType" mapstructure:"ResourceSubType"`
}

func (al *AWSActionLedger) Commit(ctx context.Context, action string, resource cloudinquisitor.PassableResource, actionError error) error {
	db, err := database.NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	var ledgerItem AWSActionLedger
	err = mapstructure.Decode(resource.GetMetadata(), &ledgerItem)
	if err != nil {
		return err
	}

	tz, _ := time.LoadLocation("UTC")
	lc, _ := lambdacontext.FromContext(ctx)
	transaction := AWSActionLedger{
		RequestID:         lc.AwsRequestID,
		LambdaFunctionArn: lc.InvokedFunctionArn,
	}

	transaction.RequestID = lc.AwsRequestID
	transaction.LambdaFunctionArn = lc.InvokedFunctionArn
	transaction.ActionTime = time.Now().In(tz)
	transaction.ActionError = actionError.Error()
	transaction.StepFunctionExecutionID = resource.StepFunctionExecutionID

	err = db.Create(&transaction)
	return err
}

func GetAWSActionLedger() AWSActionLedger {
	return AWSActionLedger{}
}
