package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	instrument "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/route53"
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
	Aliased      bool
	Alias        struct {
		ZoneId     string
		RecordName string
	}
	logger *log.Logger
}

type AWSRoute53RecordSet struct {
	RecordSet []AWSRoute53Record
	AccountID string
	ChangeId  string
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
					AliasTarget struct {
						HostedZoneId string `json:"hostedZoneId"`
						DNSName      string `json:"dNSName"`
					} `json:"aliasTarget"`
				} `json:"resourceRecordSet"`
			} `json:"changes"`
		} `json:"changeBatch"`
	} `json:"requestParameters"`
	EventId          string `json:"eventID"`
	ResponseElements struct {
		ChangeInfo struct {
			ID         string `json:"id"`
			Status     string `json:"status"`
			submitedAt string `json:"submittedAt"`
		} `json:"changeInfo"`
	} `json:"responseElements"`
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
		values := []string{}
		for _, val := range change.ResourceRecordSet.ResourceRecords {
			values = append(values, val.Value)
		}
		record := AWSRoute53Record{
			AccountID:    event.AccountID,
			ZoneID:       route53Details.RequestParameters.HostedZoneId,
			EventName:    route53Details.EventName,
			Action:       change.Action,
			RecordType:   change.ResourceRecordSet.Type,
			RecordName:   change.ResourceRecordSet.Name,
			RecordValues: values,
			Aliased:      false,
			logger:       r.logger,
		}

		if change.ResourceRecordSet.AliasTarget.DNSName != "" {
			record.Aliased = true
			record.Alias.RecordName = change.ResourceRecordSet.AliasTarget.DNSName
			record.Alias.ZoneId = change.ResourceRecordSet.AliasTarget.HostedZoneId
		}

		records = append(records, record)

	}

	r.AccountID = event.AccountID
	r.RecordSet = records
	r.ChangeId = route53Details.ResponseElements.ChangeInfo.ID

	for {
		pending, err := r.isPending()
		if !pending {
			break
		}

		if err != nil {
			r.logger.WithFields(logrus.Fields{
				"cloud-inquisitor-resource": "aws-route53-record-set",
				"cloud-inquisitor-error":    "pending error",
			}).Error(err.Error())
			return err
		}
		r.logger.WithFields(r.GetMetadata()).WithFields(
			logrus.Fields{
				"cloud-inquisitor-resource": "aws-route53-record-set",
			}).Debug("resource is still pending")

		time.Sleep(10 * time.Second)
	}

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
		}).WithFields(r.GetMetadata()).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-route53-record-set resource")
	}

	err = json.Unmarshal(structJson, r)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).WithFields(r.GetMetadata()).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-route53-record-set resource")
	}

	return nil
}

func (r *AWSRoute53RecordSet) PublishState() error {
	r.logger.WithFields(r.GetMetadata()).Debug("resource record set has no publish; calling records in set")
	for idx, record := range r.RecordSet {
		err := record.PublishState()
		if err != nil {
			r.logger.WithFields(r.GetMetadata()).WithFields(map[string]interface{}{
				"cloud-inquisitor-resource": "aws-route53-record-set",
				"cloud-inquisitor-error":    "error publishing records",
				"record-index":              idx,
				"record-name":               record.RecordName,
				"record-values":             record.RecordValues,
				"record-type":               record.RecordType,
			}).Error(err.Error())
			return err
		}
	}
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

func (r *AWSRoute53RecordSet) isPending() (bool, error) {
	// need to grab zone id
	if !settings.IsSet("assume_role") {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "missing settings value",
		}).WithFields(r.GetMetadata()).Error(errors.New("settings value assume_role not set"))
		return true, errors.New("settings value assume_role not set")
	}
	accountSession, err := AWSAssumeRole(r.AccountID, settings.GetString("assume_role"), session.New())
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "assume role error",
		}).WithFields(r.GetMetadata()).Error(err.Error())
		return true, err
	}

	route53Svc := route53.New(accountSession)
	pendingInput := &route53.GetChangeInput{
		Id: aws.String(r.ChangeId),
	}

	pendingOutput, err := route53Svc.GetChange(pendingInput)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "route53 error get change",
		}).WithFields(r.GetMetadata()).Error(err.Error())
		return true, err
	}

	switch *pendingOutput.ChangeInfo.Status {
	case "PENDING":
		return true, nil
	case "INSYNC":
		return false, nil
	}

	return true, nil
}

func (r *AWSRoute53RecordSet) AnalyzeForHijack() (*model.HijackableResourceChain, error) {
	return &model.HijackableResourceChain{}, nil
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
	for k, v := range lamdbaMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range passedInMetadata {
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
	switch r.Action {
	case "CREATE":
		err := r.createRecordEntries()
		if err != nil {
			r.logger.WithFields(logrus.Fields{
				"cloud-inquisitor-resource": "aws-route53-zone",
				"cloud-inquisitor-error":    err.Error(),
			}).WithFields(r.GetMetadata()).Error(err.Error())
		}
		return err
	case "DELETE":
	case "UPSERT":
		err := r.createRecordEntries()
		if err != nil {
			r.logger.WithFields(logrus.Fields{
				"cloud-inquisitor-resource": "aws-route53-zone",
				"cloud-inquisitor-error":    err.Error(),
			}).WithFields(r.GetMetadata()).Error(err.Error())
		}
		return err
	default:
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "unknown route53 record action",
			"route53-record-action":     r.Action,
		}).WithFields(r.GetMetadata()).Error("unknown route53 record action")
		return errors.New("unknown route53 record action")
	}
	return nil
}

func (r *AWSRoute53Record) RefreshState() error {
	// need to grab zone id
	if !settings.IsSet("assume_role") {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record",
			"cloud-inquisitor-error":    "missing settings value",
		}).WithFields(r.GetMetadata()).Error(errors.New("settings value assume_role not set"))
		return errors.New("settings value assume_role not set")
	}
	accountSession, err := AWSAssumeRole(r.AccountID, settings.GetString("assume_role"), session.New())
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record",
			"cloud-inquisitor-error":    "assume role error",
		}).WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	route53Svc := route53.New(accountSession)
	var matchingRecordSet *route53.ResourceRecordSet = nil
	err = route53Svc.ListResourceRecordSetsPages(
		&route53.ListResourceRecordSetsInput{
			HostedZoneId: aws.String(r.ZoneID),
		},
		func(output *route53.ListResourceRecordSetsOutput, last bool) bool {
			for _, recordSet := range output.ResourceRecordSets {
				r.logger.WithFields(r.GetMetadata()).WithFields(map[string]interface{}{
					"aws-route53-call": "ListResourceRecordSets",
				}).Debugf("record set: %#v", *recordSet)

				// aws events do no format record names properly
				// users do not need to end the domain with a "." and the API call provides the trailing "."
				// for record names
				if *recordSet.Name == r.RecordName || strings.HasPrefix(*recordSet.Name, r.RecordName) {
					matchingRecordSet = recordSet
					return false // immediately exits loop and func/API call
				}
			}

			return !last
		},
	)

	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "list resource records",
		}).WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	if matchingRecordSet == nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "no matching resource record set",
		}).WithFields(r.GetMetadata()).Error("no matching resource record set")
		return errors.New("no matching resource record set")
	}

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

func (r *AWSRoute53Record) createRecordEntries() error {
	db, err := graph.NewDBConnection()
	defer db.Close()
	if err != nil {
		r.logger.WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	// get account
	account := model.Account{AccountID: r.AccountID}
	err = db.FirstOrCreate(&account, account).Error
	if err != nil {
		return err
	}

	// get zone with proper account.ID
	zone := model.Zone{ZoneID: r.ZoneID, AccountID: account.ID}
	err = db.FirstOrCreate(&zone, zone).Error
	if err != nil {
		return err
	}

	// associate zones if they are not already associated
	err = db.Model(&account).Association("ZoneRelation").Append(&zone).Error
	if err != nil {
		return err
	}

	// get record
	record := model.Record{RecordID: r.RecordName, AccountID: account.ID, ZoneID: zone.ID}
	err = db.FirstOrCreate(&record, record).Error
	if record.RecordType != r.RecordType || record.Alias != r.Aliased {
		record.RecordType = r.RecordType
		record.Alias = r.Aliased
		r.GetLogger().WithFields(r.GetMetadata()).Debugf("saving record: %#v", record)
		err = db.Model(&model.Record{}).Save(&record).Error
		if err != nil {
			return err
		}
	}

	err = db.Model(&zone).Association("RecordRelation").Append(&record).Error
	if err != nil {
		return err
	}

	err = db.Model(&account).Association("RecordRelation").Append(&record).Error
	if err != nil {
		return err
	}

	for _, rawValue := range r.RecordValues {
		r.logger.Debugf("looking for value: %v", rawValue)
		// get each value
		value := model.Value{ValueID: rawValue, RecordID: record.ID}
		err = db.FirstOrCreate(&value, value).Error
		if err != nil {
			return err
		}
		r.logger.Debugf("appening value %#v to record %#v", value, record.ID)
		err = db.Model(&record).Association("ValueRelation").Append(value).Error
		if err != nil {
			return err
		}
	}

	if r.Aliased {
		r.logger.Debugf("looking for value: %v", r.Alias.RecordName)
		// get each value
		value := model.Value{ValueID: r.Alias.RecordName, RecordID: record.ID}
		err = db.FirstOrCreate(&value, value).Error
		if err != nil {
			return err
		}
		r.logger.Debugf("appening value %#v to record %#v", value, record.ID)
		err = db.Model(&record).Association("ValueRelation").Append(value).Error
		if err != nil {
			return err
		}
	}

	r.logger.WithFields(r.GetMetadata()).Debug("adding account/zone to graph")
	return nil
}

func (r *AWSRoute53Record) AnalyzeForHijack() (*model.HijackableResourceChain, error) {
	return &model.HijackableResourceChain{}, nil
}
