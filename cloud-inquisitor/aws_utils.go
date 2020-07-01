package cloudinquisitor

import (
	"context"
	"fmt"

	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/google/uuid"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sts"
)

// AWSAssumeRole - This function assumes a role in a target AWS Account and returns
// credential within the AssumeRole Output
// sess := session.Must(session.NewSession())
func AWSAssumeRole(accountID string, role string, inputSession *session.Session) (*session.Session, error) {
	if inputSession == nil {
		inputSession = session.Must(session.NewSession())
	}

	svc := sts.New(inputSession)
	arn := fmt.Sprintf("arn:aws:iam::%s:role/%s", accountID, role)
	input := &sts.AssumeRoleInput{
		RoleArn:         aws.String(arn),
		RoleSessionName: aws.String("default")}
	result, err := svc.AssumeRole(input)
	if err != nil {
		return nil, err
	}
	creds := credentials.NewStaticCredentials(
		*result.Credentials.AccessKeyId,
		*result.Credentials.SecretAccessKey,
		*result.Credentials.SessionToken,
	)
	assumedSession := session.Must(
		session.NewSession(&aws.Config{
			Credentials: creds}),
	)
	return assumedSession, nil
}

func DefaultLambdaMetadata(componentName string, ctx context.Context) (map[string]interface{}, error) {
	var lambdaExecutionID string

	if awsContext, ok := lambdacontext.FromContext(ctx); ok {
		lambdaExecutionID = awsContext.AwsRequestID
	} else {
		sessionUUID, uuidErr := uuid.NewRandom()
		if uuidErr != nil {
			return map[string]interface{}{}, uuidErr
		}
		lambdaExecutionID = sessionUUID.String()
	}

	workflowUUID, err := uuid.NewRandom()
	if err != nil {
		return map[string]interface{}{}, err
	}

	metadata := map[string]interface{}{
		"cloud-inquisitor-workflow-uuid": workflowUUID.String(),
		"cloud-inquisitor-step-uuid":     lambdaExecutionID,
		"cloud-inquisitor-component":     componentName,
		"aws-lambda-execution-id":        lambdaExecutionID,
	}

	return metadata, nil
}
