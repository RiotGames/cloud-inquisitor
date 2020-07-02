package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.PassableResource) (cloudinquisitor.PassableResource, error) {
	metadata, err := cloudinquisitor.LambdaMetadataFromPassableResource("tag_auditor", ctx, resource)
	if err != nil {
		if err != nil {
			return resource, err
		}
	}

	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: metadata,
	}
	logger := instrument.GetInstrumentedLogger(opts, ctx)
	parsedResource, err := resource.GetResource(logger)
	if err != nil {
		logger.WithFields(logrus.Fields{"cloud-inquisitor-error": "resource parsing error"}).Error(err.Error(), nil)
		return resource, nil
	}

	err = parsedResource.RefreshState(logger)
	if err != nil {
		logger.WithFields(logrus.Fields{"cloud-inquisitor-error": "resource refresh error"}).Error(err.Error(), nil)
		return resource, nil
	}

	action, err := parsedResource.Audit(logger)
	if err != nil {
		logger.WithFields(logrus.Fields{"cloud-inquisitor-error": "resource audit error"}).Error(err.Error(), nil)
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Finished: true,
		}, nil
	}

	if err := parsedResource.TakeAction(action, logger); err != nil {
		logger.WithFields(logrus.Fields{"cloud-inquisitor-error": "resource action error"}).Error(err.Error(), nil)
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Finished: true,
		}, nil
	}

	if err := parsedResource.PublishState(logger); err != nil {
		logger.WithFields(logrus.Fields{"cloud-inquisitor-error": "resource publish state"}).Warn(err.Error(), nil)
	}

	if err := parsedResource.SendMetrics(logger); err != nil {
		logger.WithFields(logrus.Fields{"cloud-inquisitor-error": "resource metrics error"}).Error(err.Error(), nil)
	}

	return cloudinquisitor.PassableResource{
		Resource: parsedResource,
		Type:     parsedResource.GetType(),
		Finished: false,
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
