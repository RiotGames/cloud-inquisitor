package main

import (
	"context"
	"errors"
	"reflect"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.PassableResource) (cloudinquisitor.PassableResource, error) {

	parsedResource, err := resource.GetHijackableResource(ctx, map[string]interface{}{
		"cloud-inquisitor-component": "hijack-graph-updater",
	})
	if err != nil {
		return resource, err
	}

	err = parsedResource.RefreshState()
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

	if reflect.DeepEqual((cloudinquisitor.HijackChain{}), hijackChain) {
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Metadata: parsedResource.GetLogger().GetMetadata(),
			Finished: true,
		}, errors.New("hijack analysis returned nil hijack chain")
	}

	if len(hijackChain.Chain) > 0 {
		// send notification
	}

	err = parsedResource.PublishState()
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
		Finished: true,
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
