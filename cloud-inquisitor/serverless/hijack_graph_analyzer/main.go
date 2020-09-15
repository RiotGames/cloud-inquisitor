package main

import (
	"context"
	"errors"
	"fmt"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/notification"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.PassableResource) (cloudinquisitor.PassableResource, error) {

	parsedResource, err := resource.GetHijackableResource(ctx, map[string]interface{}{
		"cloud-inquisitor-component": "hijack-graph-updater",
	})
	if err != nil {
		return resource, err
	}

	hijackChain, err := parsedResource.AnalyzeForHijack()
	if err != nil {
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Metadata: parsedResource.GetLogger().GetMetadata(),
			Finished: true,
		}, err
	}

	logger := parsedResource.GetLogger()
	if logger.L.GetLevel() == logrus.DebugLevel {
		logger.Debugf("hijack chain for resource with metadata: %#v", parsedResource.GetMetadata())
		logger.Debugf("root hijack element: %#v", *hijackChain.Resource)
		for idx, hijackElement := range hijackChain.Upstream {
			logger.Debugf("upstream hijack element %v: %#v", idx, *hijackElement)
		}
		for idx, hijackElement := range hijackChain.Downstream {
			logger.Debugf("downstream hijack element %v: %#v", idx, *hijackElement)
		}
	}

	if len(hijackChain.Upstream) > 0 || len(hijackChain.Downstream) > 0 {
		// send notification
		content := notification.GenerateContent(hijackChain)
		sendTo := settings.GetString("simple_email_service.verified_email")
		msg, err := notification.NewHijackNotficationMessage("Potential DNS Hijack", []string{sendTo}, []string{sendTo}, content)
		if err != nil {
			return cloudinquisitor.PassableResource{
				Resource: parsedResource,
				Type:     parsedResource.GetType(),
				Metadata: parsedResource.GetLogger().GetMetadata(),
				Finished: true,
			}, fmt.Errorf("error generating hijack message: %s", err.Error())
		}

		notifier, err := notification.NewNotifier()
		if err != nil {
			return cloudinquisitor.PassableResource{
				Resource: parsedResource,
				Type:     parsedResource.GetType(),
				Metadata: parsedResource.GetLogger().GetMetadata(),
				Finished: true,
			}, errors.New("unable to get notifier to notify of potential hijack")
		}

		_, err = notifier.SendNotification(msg)
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Metadata: parsedResource.GetLogger().GetMetadata(),
			Finished: true,
		}, err
	}

	if err != nil {
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Metadata: parsedResource.GetLogger().GetMetadata(),
			Finished: true,
		}, err
	}

	return cloudinquisitor.PassableResource{
		Resource: parsedResource,
		Type:     parsedResource.GetType(),
		Metadata: parsedResource.GetLogger().GetMetadata(),
		Finished: false,
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
