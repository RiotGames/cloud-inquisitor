package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"

	log "github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, event events.CloudWatchEvent) (cloudinquisitor.Resource, error) {
	resource, _ := cloudinquisitor.NewResource(event)
	log.Printf("resource: %#v\n", resource)
	return resource, nil
}

func main() {
	lambda.Start(handlerRequest)
}
