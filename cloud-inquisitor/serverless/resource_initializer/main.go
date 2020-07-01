package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"

	"github.com/sirupsen/logrus"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func handlerRequest(ctx context.Context, event events.CloudWatchEvent) (cloudinquisitor.PassableResource, error) {

	metadata, err := cloudinquisitor.DefaultLambdaMetadata("resource-initializer", ctx)
	if err != nil {
		return cloudinquisitor.PassableResource{}, err
	}

	metadata["aws-intial-event-id"] = event.ID
	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: metadata,
	}
	logger := instrument.GetInstrumentedLogger(opts, ctx)

	resource, _ := cloudinquisitor.NewResource(event)
	logger.WithFields(logrus.Fields(resource.GetMetadata())).Debug("New resource created")

	if settings.GetString("stub_resources") != "enabled" {
		return cloudinquisitor.PassableResource{
			Resource: resource,
			Type:     resource.GetType(),
			Finished: true,
			Metadata: metadata,
		}, nil
	}
	return cloudinquisitor.PassableResource{
		Resource: resource,
		Type:     resource.GetType(),
		Finished: false,
		Metadata: metadata,
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
