package ledger

import "github.com/aws/aws-lambda-go/events"

type ActionLedger interface {
	Commit() error
}

func GetActionLedger() (ActionLedger, error) ActionLedger {
	return GetAWSActionLedger()
}
