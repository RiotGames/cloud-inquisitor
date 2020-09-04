package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

type auditorPayload struct {
	PassableResource  cloudinquisitor.PassableResource `json:"PassableResource"`
	StepFunctionExeID string                           `json:"StepFunctionExeID"`
}

func handlerRequest(ctx context.Context, payload auditorPayload) (cloudinquisitor.PassableResource, error) {
	resource := payload["PassableResource"]

	parsedResource, err := resource.GetTaggableResource(ctx, map[string]interface{}{
		"cloud-inquisitor-component": "tag-auditor",
	})
	if err != nil {
		return resource, nil
	}

	err = parsedResource.RefreshState()
	if err != nil {
		return resource, nil
	}

	action, err := parsedResource.Audit()
	if err != nil {
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Metadata: parsedResource.GetLogger().GetMetadata(),
			Finished: true,
		}, nil
	}

	actionError := parsedResource.TakeAction(action)
	graph.ActionLedgerCommit(
		ctx, 
		action, 
		parsedResource.GetMetadata(), 
		actionError, 
		payload["StepFunctionExeID"]
	)

	if actionError != nil {
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Metadata: parsedResource.GetLogger().GetMetadata(),
			Finished: true,
		}, nil
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
