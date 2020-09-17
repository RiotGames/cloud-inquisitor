package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database"
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

type AWSRoute53Zone struct {
	AccountID string
	ZoneName  string
	ZoneID    string
	EventName string
	ChangeId  string
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
	EventId          string `json:"eventID"`
	ResponseElements struct {
		HostedZone struct {
			ID     string `json:"id"`
			Name   string `json:"name"`
			Config struct {
				Comment     string `json:"comment"`
				PrivateZone bool   `json:"privateZone"`
			} `json:"config"`
		} `json:"hostedZone"`
		ChangeInfo struct {
			ID          string `json:"id"`
			Status      string `json:"status"`
			SubmittedAt string `json:"submittedAt"`
		} `json:"changeInfo"`
	} `json:"responseElements"`
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
	r.ZoneName = route53Details.ResponseElements.HostedZone.Name
	if strings.HasPrefix(route53Details.ResponseElements.HostedZone.ID, "/hostedzone/") {
		r.ZoneID = strings.ReplaceAll(route53Details.ResponseElements.HostedZone.ID, "/hostedzone/", "")
	} else {
		r.ZoneID = route53Details.ResponseElements.HostedZone.ID
	}
	r.Type = SERVICE_AWS_ROUTE53_ZONE
	r.EventName = route53Details.EventName
	r.ChangeId = route53Details.ResponseElements.ChangeInfo.ID

	for {
		pending, err := r.isPending()
		if !pending {
			break
		}

		if err != nil {
			r.logger.WithFields(logrus.Fields{
				"cloud-inquisitor-resource": "aws-route53-zone",
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

func (r *AWSRoute53Zone) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
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
	if !settings.IsSet("assume_role") {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "missing settings value",
		}).WithFields(r.GetMetadata()).Error(errors.New("settings value assume_role not set"))
		return errors.New("settings value assume_role not set")
	}
	accountSession, err := AWSAssumeRole(r.AccountID, settings.GetString("assume_role"), session.New())
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "assume role error",
		}).WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	route53Svc := route53.New(accountSession)
	// get route53 zone that most closely matches
	var matchingZone *route53.HostedZone = nil
	listByNameOutput, err := route53Svc.ListHostedZonesByName(&route53.ListHostedZonesByNameInput{
		DNSName: aws.String(r.ZoneName),
	})
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "list hosted zone by name",
		}).WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	for _, zone := range listByNameOutput.HostedZones {
		if *zone.Name == r.ZoneName || strings.HasPrefix(*zone.Name, r.ZoneName) {
			matchingZone = zone
			break
		}
	}

	if matchingZone == nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-zone",
			"cloud-inquisitor-error":    "no matching zone found",
		}).WithFields(r.GetMetadata()).Error("no matching zone found")
		return errors.New("no matching zone found")
	}

	if strings.HasPrefix(*matchingZone.Id, "/hostedzone/") {
		r.ZoneID = strings.ReplaceAll(*matchingZone.Id, "/hostedzone/", "")
	} else {
		r.ZoneID = *matchingZone.Id
	}
	r.ZoneName = *matchingZone.Name

	return nil
}

func (r *AWSRoute53Zone) PublishState() error {
	switch r.EventName {
	case "CreateHostedZone":
		return r.createZoneEntries()
	case "DeleteHostedZone":
		// implement removal
		return nil
	default:
		return nil
	}
	return nil
}

func (r *AWSRoute53Zone) createZoneEntries() error {
	db, err := database.NewDBConnection()
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
	r.GetLogger().WithFields(r.GetMetadata()).Debugf("found account: %#v", account)

	zone := model.Zone{ZoneID: r.ZoneID, AccountID: account.ID}
	err = db.FirstOrCreate(&zone, zone).Error
	if err != nil {
		return err
	}
	r.GetLogger().WithFields(r.GetMetadata()).Debugf("found  zone: %#v", zone)

	if zone.Name != r.ZoneName || zone.ServiceType != r.GetType() {
		zone.Name = r.ZoneName
		zone.ServiceType = r.GetType()
		err = db.Model(&model.Zone{}).Updates(&zone).Error
		if err != nil {
			return err
		}
	}

	// add zone to account
	err = db.Model(&account).Where(&account).Association("ZoneRelation").Append(zone).Error
	if err != nil {
		return err
	}

	r.logger.WithFields(r.GetMetadata()).Debug("adding account/zone to graph")
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
		"zone-id":     r.ZoneID,
		"event":       r.EventName,
		"serviceType": r.Type,
	}
}
func (r *AWSRoute53Zone) GetLogger() *log.Logger {
	return r.logger
}

func (r *AWSRoute53Zone) isPending() (bool, error) {
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

func (r *AWSRoute53Zone) AnalyzeForHijack() (*model.HijackableResourceChain, error) {
	return &model.HijackableResourceChain{}, nil
}
