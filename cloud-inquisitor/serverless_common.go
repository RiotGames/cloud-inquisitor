package cloudinquisitor

import "github.com/aws/aws-lambda-go/events"

type StepFunctionInitPayload struct {
	CloudWatchEvent         events.CloudWatchEvent `json:"CloudWatchEvent"`
	StepFunctionExecutionID string                 `json:"StepFunctionExeID"`
}
