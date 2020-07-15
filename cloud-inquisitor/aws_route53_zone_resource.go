package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-lambda-go/events"
	"github.com/sirupsen/logrus"
)

type AWSRoute53Zone struct {
	AccountID string
	ZoneName  string
	ZoneID    string
	EventName string
	Type      Service

	logger *log.Logger
}

type AWSRoute53ZoneEventBusDetail struct {
	EventName         string `json:"eventName"`
	ErrorCode         string `json:"errorCode"`
	ErrorMessage      string `json:"errorMessage"`
	RequestParameters struct {
		Name             string `json:"name"`
		HostedZoneConfig struct {
			Comment     string `json:"comment"`
			PrivateZone bool   `json:"privateZone"`
		} `json:"hostedZoneConfig"`
	} `json:"requestParameters"`
	EventId string `json:"eventID"`
}

func (r *AWSRoute53Zone) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passedInMetadata map[string]interface{}) error {
	defaultMetadata, err := DefaultLambdaMetadata(ctx)
	if err != nil {
		return err
	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range defaultMetadata {
		mergedMetaData[k] = v
	}

	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}
	r.logger = instrument.GetInstrumentedLogger(opts, ctx)

	var route53Details AWSRoute53ZoneEventBusDetail
	err = json.Unmarshal(event.Detail, &route53Details)
	if err != nil {
		r.logger.Error(err.Error(), nil)
		return err
	}

	r.AccountID = event.AccountID
	r.ZoneName = route53Details.RequestParameters.Name
	r.Type = SERVICE_AWS_ROUTE53_ZONE
	r.EventName = route53Details.EventName

	return nil
}

func (r *AWSRoute53Zone) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
	lamdbaMetadata, err := LambdaMetadataFromPassableResource(ctx, resource)
	if err != nil {
		return err
	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range lamdbaMetadata {
		mergedMetaData[k] = v
	}
	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}
	r.logger = instrument.GetInstrumentedLogger(opts, ctx)
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "json marshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-route53-zone resource")
	}

	err = json.Unmarshal(structJson, r)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-route53-zone resource")
	}

	return nil
}

func (r *AWSRoute53Zone) RefreshState() error {
	// need to grab zone id
	return nil
}
func (r *AWSRoute53Zone) PublishState() error {
	r.logger.WithFields(r.GetMetadata()).Debug("starting graph connection")
	gClient, err := graph.NewGraph()
	if err != nil {
		r.logger.WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	r.logger.WithFields(r.GetMetadata()).WithFields(map[string]interface{}{
		"subject":   r.ZoneName,
		"predicate": "is-owned-by",
		"object":    r.AccountID,
	}).Debug("adding quad to graph")
	gClient.AddQuad(r.ZoneName, "is-owned-by", r.AccountID)

	r.logger.WithFields(r.GetMetadata()).WithFields(map[string]interface{}{
		"subject":   r.ZoneName,
		"predicate": "is-service-type",
		"object":    r.GetType(),
	}).Debug("adding quad to graph")
	gClient.AddQuad(r.ZoneName, "is-service-type", r.GetType())
	return nil
}

func (r *AWSRoute53Zone) GetType() Service {
	return SERVICE_AWS_ROUTE53_ZONE
}

func (r *AWSRoute53Zone) SendNotification() error {
	return nil
}

func (r *AWSRoute53Zone) GetMetadata() map[string]interface{} {
	return map[string]interface{}{
		"account":     r.AccountID,
		"zone":        r.ZoneName,
		"event":       r.EventName,
		"serviceType": r.Type,
	}
}
func (r *AWSRoute53Zone) GetLogger() *log.Logger {
	return r.logger
}
