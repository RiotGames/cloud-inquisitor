package ledger

import (
	"context"
	"time"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database"
	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/jinzhu/gorm"
	"github.com/mitchellh/mapstructure"
)

type AWSActionLedgerEntry struct {
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

func (al AWSActionLedgerEntry) Commit(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) error {
	db, err := database.NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}

	al.enrich(ctx, resource, action, actionError)
	db.Create(&al)

	err = db.Close()
	return err
}

func (al AWSActionLedgerEntry) enrich(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) error {

	lambdaContext := ctx.(context.Context)

	// Fill in context metadata
	err := mapstructure.Decode(ctx, &al)
	if err != nil {
		return err
	}

	// Fill in resoure metadata
	err = mapstructure.Decode(resource.Metadata, &al)
	if err != nil {
		return err
	}

	// Fill in misc information
	tz, _ := time.LoadLocation("UTC")
	lc, _ := lambdacontext.FromContext(lambdaContext)

	al.RequestID = lc.AwsRequestID
	al.LambdaFunctionArn = lc.InvokedFunctionArn
	al.ActionTime = time.Now().In(tz)
	al.ActionError = actionError.Error()
	al.StepFunctionExecutionID = resource.StepFunctionExecutionID

	return nil
}

func GetAWSActionLedger() AWSActionLedgerEntry {
	return AWSActionLedgerEntry{}
}
