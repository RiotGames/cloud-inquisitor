package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"
	"github.com/sirupsen/logrus"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/google/uuid"
)

func handlerRequest(ctx context.Context, event events.CloudWatchEvent) (cloudinquisitor.PassableResource, error) {
	workflowUUID, err := uuid.NewRandom()
	if err != nil {
		return cloudinquisitor.PassableResource{}, err
	}

	sessionUUID, err := uuid.NewRandom()
	if err != nil {
		return cloudinquisitor.PassableResource{}, err
	}

	opts := log.LoggerOpts{
		Level: log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: map[string]interface{}{
			"workflow-uuid": workflowUUID,
			"session-uuid":  sessionUUID,
			"cloud-inquisitor-component": "resource-initializer"
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
	return cloudinquisitor.PassableResource{
		Resource: resource,
		Type:     resource.GetType(),
		Finished: false,
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
