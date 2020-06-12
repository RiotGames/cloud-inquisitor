package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"
	"github.com/sirupsen/logrus"

	"github.com/google/uuid"
	//"github.com/aws/aws-lambda-go/lambda"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"

	log "github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, event events.CloudWatchEvent) (cloudinquisitor.PassableResource, error) {
	workflowUUID, err := uuid.NewRandom()
	if err != nil {
		return cloudinquisitor.PassableResource{}, err
	}
	
	if sessionUUID, err := uuid.NewRandom()
	if err != nil {
		return cloudinquisitor.PassableResource{}, err
	}
	
	opts := &logger.LoggerOpts{
		Level: logrus.InfoLevel,
		Metadata: map[string]interface{}{
			"workflow-uuid": workflowUUID,
			"session-uuid": sessionUUID,
		}
	}
	
	logger := newrelic.NewLambdaLogger(opts)
	txn := newrelic.GetTxnFromLambdaContext(ctx)
	
	resourceCtx := newrelic.NewContextFromTxn(txn, logger)
	logger.WithContext(resourceCtx).Info("Create new resource")
	resource, _ := cloudinquisitor.NewResource(event)
	logger.WithContext(resourceCtx).WithFields(logrus.Fields(resource.GetMetaData())).Info("New resource created")
	return cloudinquisitor.PassableResource{
		Resource: resource,
		Type:     resource.GetType(),
		Finished: false,
	}, nil
}

func main() {
	//lambda.Start(handlerRequest)
	newrelic.StartNewRelicLambda(handlerRequest())
}
