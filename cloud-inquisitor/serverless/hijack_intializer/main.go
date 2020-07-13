package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func handlerRequest(ctx context.Context, event events.CloudWatchEvent) (cloudinquisitor.PassableResource, error) {
	resource, _ := cloudinquisitor.NewHijackableResource(event, ctx, map[string]interface{}{
		"aws-intial-event-id":        event.ID,
		"cloud-inquisitor-component": "hijack-initializer",
	})

	if resource.GetType() == cloudinquisitor.SERVICE_STUB && settings.GetString("stub_resources") != "enabled" {
		return cloudinquisitor.PassableResource{
			Resource: resource,
			Type:     resource.GetType(),
			Finished: true,
			Metadata: resource.GetLogger().GetMetadata(),
		}, nil
	}
	return cloudinquisitor.PassableResource{
		Resource: resource,
		Type:     resource.GetType(),
		Finished: false,
		Metadata: resource.GetLogger().GetMetadata(),
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
