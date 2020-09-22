package main

import (
	"context"
	"errors"

	cloudinquisitor "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

type passableResourcesStruct struct {
	Resources []cloudinquisitor.PassableResource `json:"resources"`
}

func handlerRequest(ctx context.Context, payload cloudinquisitor.StepFunctionInitPayload) (passableResourcesStruct, error) {
	event := payload.CloudWatchEvent
	sfnExeID := payload.StepFunctionExecutionID

	resource, err := cloudinquisitor.NewHijackableResource(event, ctx, map[string]interface{}{
		"aws-intial-event-id":        event.ID,
		"cloud-inquisitor-component": "hijack-initializer",
	})

	if err != nil {
		return passableResourcesStruct{}, err
	}

	err = resource.RefreshState()
	if err != nil {
		return passableResourcesStruct{}, err
	}

	if resource.GetType() == cloudinquisitor.SERVICE_STUB && settings.GetString("stub_resources") != "enabled" {
		return passableResourcesStruct{[]cloudinquisitor.PassableResource{
			cloudinquisitor.PassableResource{
				Resource:                resource,
				Type:                    resource.GetType(),
				Finished:                true,
				Metadata:                resource.GetLogger().GetMetadata(),
				StepFunctionExecutionID: sfnExeID,
			},
		}}, nil
	}

	passableResources := []cloudinquisitor.PassableResource{}
	switch resource.GetType() {
	case cloudinquisitor.SERVICE_AWS_ROUTE53_RECORD_SET:
		for _, record := range resource.(*cloudinquisitor.AWSRoute53RecordSet).RecordSet {
			passableResources = append(passableResources, cloudinquisitor.PassableResource{
				Resource:                record,
				Type:                    record.GetType(),
				Finished:                false,
				Metadata:                record.GetLogger().GetMetadata(),
				StepFunctionExecutionID: sfnExeID,
			})
		}
	case cloudinquisitor.SERVICE_AWS_ROUTE53_ZONE, cloudinquisitor.SERVICE_AWS_CLOUDFRONT, cloudinquisitor.SERVICE_AWS_ELASTICBEANSTALK, cloudinquisitor.SERVICE_AWS_S3:
		passableResources = append(passableResources, cloudinquisitor.PassableResource{
			Resource:                resource,
			Type:                    resource.GetType(),
			Finished:                false,
			Metadata:                resource.GetLogger().GetMetadata(),
			StepFunctionExecutionID: sfnExeID,
		})
	default:
		return passableResourcesStruct{passableResources}, errors.New("unknown resource type " + resource.GetType())
	}
	return passableResourcesStruct{passableResources}, nil
}

func main() {
	newrelic.StartNewRelicLambda(handlerRequest, settings.GetString("name"))
}
