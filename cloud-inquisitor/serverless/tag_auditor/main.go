package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/lambda"

	log "github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.PassableResource) (cloudinquisitor.PassableResource, error) {
	log.Printf("resource: %#v\n", resource)
	parsedResource, err := resource.GetResource()
	if err != nil {
		log.Warn(err.Error())
		return resource, nil
	}

	err = parsedResource.RefreshState()

	action, err := parsedResource.Audit()
	if err != nil {
		log.Warn(err.Error())
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Finished: true,
		}, nil
	}

	if err := parsedResource.TakeAction(action); err != nil {
		log.Warn(err.Error())
		return cloudinquisitor.PassableResource{
			Resource: parsedResource,
			Type:     parsedResource.GetType(),
			Finished: true,
		}, nil
	}

	if err := parsedResource.PublishState(); err != nil {
		log.Warn(err.Error())
	}

	if err := parsedResource.SendMetrics(); err != nil {
		log.Warn(err.Error())
	}

	return cloudinquisitor.PassableResource{
		Resource: parsedResource,
		Type:     parsedResource.GetType(),
		Finished: false,
	}, nil
}

func main() {
	lambda.Start(handlerRequest)
}
