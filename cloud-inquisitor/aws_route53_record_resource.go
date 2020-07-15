package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-lambda-go/events"
	"github.com/sirupsen/logrus"
)

type AWSRoute53Record struct {
	AccountID    string
	ZoneID       string
	EventName    string
	Action       string
	RecordType   string
	RecordName   string
	RecordValues []string
	logger       *log.Logger
}

type AWSRoute53RecordSet struct {
	RecordSet []AWSRoute53Record
	logger    *log.Logger
}

type AWSRoute53RecordSetEventBusDetail struct {
	EventName         string `json:"eventName"`
	ErrorCode         string `json:"errorCode"`
	ErrorMessage      string `json:"errorMessage"`
	RequestParameters struct {
		HostedZoneId string `json:"hostedZoneId"`
		ChangeBatch  struct {
			Changes []struct {
				Action            string `json:"action"`
				ResourceRecordSet struct {
					Name            string `json:"Name"`
					Type            string `json:"type"`
					TTL             int    `json:"tTL"`
					ResourceRecords []struct {
						Value string `json:"value"`
					} `json:"resourceRecords"`
				} `json:"resourceRecordSet"`
			} `json:"changes"`
		} `json:"changeBatch"`
	} `json:"requestParameters"`
	EventId string `json:"eventID"`
}

func (r *AWSRoute53RecordSet) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passedInMetadata map[string]interface{}) error {
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

	var route53Details AWSRoute53RecordSetEventBusDetail
	err = json.Unmarshal(event.Detail, &route53Details)
	if err != nil {
		r.logger.Error(err.Error(), nil)
		return err
	}

	records := []AWSRoute53Record{}
	for _, change := range route53Details.RequestParameters.ChangeBatch.Changes {
		record := AWSRoute53Record{
			AccountID:    event.AccountID,
			ZoneID:       route53Details.RequestParameters.HostedZoneId,
			EventName:    route53Details.EventName,
			Action:       change.Action,
			RecordType:   change.ResourceRecordSet.Type,
			RecordName:   change.ResourceRecordSet.Name,
			RecordValues: []string{},
			logger:       r.logger,
		}

		records = append(records, record)

	}

	r.RecordSet = records
	return nil
}

func (r *AWSRoute53RecordSet) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
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
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "json marshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-route53-record-set resource")
	}

	err = json.Unmarshal(structJson, r)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-route53-record-set resource")
	}

	return nil
}

func (r *AWSRoute53RecordSet) PublishState() error {
	return nil
}

func (r *AWSRoute53RecordSet) RefreshState() error {
	return nil
}

func (r *AWSRoute53RecordSet) SendNotification() error {
	return nil
}

func (r *AWSRoute53RecordSet) GetType() Service {
	return SERVICE_AWS_ROUTE53_RECORD_SET
}

func (r *AWSRoute53RecordSet) GetMetadata() map[string]interface{} {
	records := make([]map[string]interface{}, len(r.RecordSet))
	for idx, set := range r.RecordSet {
		records[idx] = set.GetMetadata()
	}
	return map[string]interface{}{
		"recordSet": records,
	}
}

func (r *AWSRoute53RecordSet) GetLogger() *log.Logger {
	return r.logger
}

func (r *AWSRoute53Record) NewFromEventBus(_ events.CloudWatchEvent, _ context.Context, _ map[string]interface{}) error {
	// this is a stub since the event for record creation is wrapped in Route53 Record Set event
	return nil
}

func (r *AWSRoute53Record) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
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
			"cloud-inquisitor-resource": "aws-route53-record",
			"cloud-inquisitor-error":    "json marshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-route53-record resource")
	}

	err = json.Unmarshal(structJson, r)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-route53-zone resource")
	}

	return nil
}

func (r *AWSRoute53Record) PublishState() error {
	return nil
}

func (r *AWSRoute53Record) RefreshState() error {
	return nil
}

func (r *AWSRoute53Record) SendNotification() error {
	return nil
}

func (r *AWSRoute53Record) GetType() Service {
	return SERVICE_AWS_ROUTE53_RECORD
}

func (r *AWSRoute53Record) GetMetadata() map[string]interface{} {
	return map[string]interface{}{
		"account":      r.AccountID,
		"zoneId":       r.ZoneID,
		"eventName":    r.EventName,
		"action":       r.Action,
		"recordType":   r.RecordType,
		"recordName":   r.RecordName,
		"recordValues": r.RecordValues,
	}
}

func (r *AWSRoute53Record) GetLogger() *log.Logger {
	return r.logger
}
