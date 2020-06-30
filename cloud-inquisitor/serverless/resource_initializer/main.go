package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/sirupsen/logrus"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/google/uuid"
)

func handlerRequest(ctx context.Context, event events.CloudWatchEvent) (cloudinquisitor.PassableResource, error) {
	var lambdaExecutionID string

	awsContext, err := lambdacontext.FromContext(ctx)
	if err != nil {
		sessionUUID, uuidErr := uuid.NewRandom()
		if uuidErr != nil {
			return cloudinquisitor.PassableResource{}, err
		}
		lambdaExecutionID = sessionUUID.String()
	}

	lambdaExecutionID = awsContext.AwsRequestID

	workflowUUID, err := uuid.NewRandom()
	if err != nil {
		return cloudinquisitor.PassableResource{}, err
	}

	opts := log.LoggerOpts{
		Level: log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: map[string]interface{}{
			"cloud-inquisitor-workflow-uuid": workflowUUID.String(),
			"cloud-inquisitor-step-uuid":     lambdaExecutionID,
			"cloud-inquisitor-component":     "resource-initializer",
			"aws-intial-event-id":            event.ID,
			"aws-lambda-execution-id":        lambdaExecutionID,
		},
	}

	hookOpts := newrelic.DefaultNewRelicHookOpts
	hookOpts.License = settings.GetString("newrelic.license")
	hookOpts.ApplicationName = settings.GetString("name")

	hookLogger := log.NewLogger(opts)
	hookLogger.L.AddHook(newrelic.NewNewRelicHook(hookOpts))

	logger := newrelic.ApplicationLogger(opts, ctx)
	resource, _ := cloudinquisitor.NewResource(event)
	logger.WithFields(logrus.Fields(resource.GetMetadata())).Debug("New resource created")
	txn := newrelic.GetTxnFromLambdaContext(ctx, hookLogger)
	txnCtx := newrelic.NewContextFromTxn(txn, hookLogger)
	hookLogger.WithContext(txnCtx).Debug("appended new context")
	hookLogger.WithFields(logrus.Fields(resource.GetMetadata())).Debug("New resource created")

	if settings.GetString("stub_resources") != "enabled" {
		return cloudinquisitor.PassableResource{
			Resource: resource,
			Type:     resource.GetType(),
			Finished: true,
			Metadata: map[string]interface{}{
				"cloud-inquisitor-workflow-uuid": workflowUUID,
				"aws-intial-event-id":            event.ID,
			},
		}, nil
	}
	return cloudinquisitor.PassableResource{
		Resource: resource,
		Type:     resource.GetType(),
		Finished: false,
		Metadata: map[string]interface{}{
			"cloud-inquisitor-workflow-uuid": workflowUUID,
			"aws-intial-event-id":            event.ID,
		},
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
