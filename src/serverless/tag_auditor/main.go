package main

import (
	"context"

	"github.com/aws/aws-lambda-go/lambda"

	log "github.com/sirupsen/logrus"
)

func handlerRequest(ctx context.Context, event interface{}) error {
	log.Printf("event: %#v\n", event)
	return nil
}

func main() {
	lambda.Start(handlerRequest)
}
