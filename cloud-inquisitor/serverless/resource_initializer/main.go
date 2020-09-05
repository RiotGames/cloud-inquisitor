package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/serverless"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func handlerRequest(ctx context.Context, payload serverless.StepFunctionInitPayload) (cloudinquisitor.PassableResource, error) {
	event := payload["CloudWatchEvent"]
	sfnExeId = payload["StepFunctionExecutionID"],

	resource, _ := cloudinquisitor.NewTaggableResource(event, ctx, map[string]interface{}{
		"aws-intial-event-id":        event.ID,
		"cloud-inquisitor-component": "resource-initializer",
	})

	if resource.GetType() == cloudinquisitor.SERVICE_STUB && settings.GetString("stub_resources") != "enabled" {
		return cloudinquisitor.PassableResource{
			Resource:                resource,
			Type:                    resource.GetType(),
			Finished:                true,
			Metadata:                resource.GetLogger().GetMetadata(),
			StepFunctionExecutionID: sfnExeId,
		}, nil
	}
	return cloudinquisitor.PassableResource{
		Resource:                resource,
		Type:                    resource.GetType(),
		Finished:                false,
		Metadata:                resource.GetLogger().GetMetadata(),
		StepFunctionExecutionID: sfnExeId,
	}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
