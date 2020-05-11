package main

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"

	log "github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, resource cloudinquisitor.Resource) (Resource, error) {
	log.Printf("resource: %#v\n", resource)
	return resource, nil
}

func main() {
	lambda.Start(handlerRequest)
}
