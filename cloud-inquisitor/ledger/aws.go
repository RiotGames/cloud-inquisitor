package ledger

import (
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
	ResourceARN             string    `json:"ResourceARN" mapstructure:"ResourceARN"`
	ResourceID              string    `json:"ResourceID" mapstructure:"ResourceID"`
	ResourceName            string    `json:"ResourceName" mapstructure:"ResourceName"`
	ResourceType            string    `json:"ResourceType" mapstructure:"ResourceType"`
	ResourceSubType         string    `json:"ResourceSubType" mapstructure:"ResourceSubType"`
}

type AWSActionLedger struct {
}

func (al AWSActionLedger) Commit(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) error {
	db, err := database.NewDBConnection()
	if err != nil {
		if db != nil {
			db.Close()
		}
		return err
	}
	defer db.Close()

	ledgerEntry, err := al.generateEntry(ctx, resource, action, actionError)
	if err != nil {
		return err
	}
	db.Create(&ledgerEntry)
	return err
}

func (al *AWSActionLedger) generateEntry(ctx interface{}, resource cloudinquisitor.PassableResource, action string, actionError error) (AWSActionLedgerEntry, error) {

	var ledgerEntry AWSActionLedgerEntry
	lc := ctx.(lambdacontext.LambdaContext)

	// Fill in resoure metadata
	err := mapstructure.Decode(resource.Metadata, &ledgerEntry)
	if err != nil {
		return ledgerEntry, err
	}
	// Fill in misc information
	tz, _ := time.LoadLocation("UTC")

	ledgerEntry.RequestID = lc.AwsRequestID
	ledgerEntry.LambdaFunctionArn = lc.InvokedFunctionArn
	ledgerEntry.ActionTime = time.Now().In(tz)
	ledgerEntry.ActionError = actionError.Error()
	ledgerEntry.StepFunctionExecutionID = resource.StepFunctionExecutionID

	return ledgerEntry, nil
}

func GetAWSActionLedger() AWSActionLedger {
	return AWSActionLedger{}
}
