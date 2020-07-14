package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.PassableResource) (cloudinquisitor.PassableResource, error) {

	parsedResource, err := resource.GetResource(ctx, map[string]interface{}{
		"cloud-inquisitor-component": "hijack-graph-updater",
	})
	if err != nil {
		return resource, err
	}

	err = parsedResource.RefreshState()
	if err != nil {
		return resource, err
	}

	parsedResource.PublishState()

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
