package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/ledger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.PassableResource) (cloudinquisitor.PassableResource, error) {

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
	actionLeger := ledger.GetActionLedger()
	actionLeger.Enrich(
		ctx,
		action,
		resource,
		actionError,
	)
	actionLedger.Commit()

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
