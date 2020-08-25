package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"reflect"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	instrument "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-lambda-go/events"
	"github.com/sirupsen/logrus"
)

type AWSCloudFrontDistributionResource struct {
	AccountID      string
	DistributionID string
	DomainName     string
	EventName      string
	Origins        []AWSCloudFrontOrigin
	logger         *log.Logger
}

type AWSCloudFrontOrigin struct {
	ID     string
	Domain string
}

type AWSCloudFrontDetail struct {
	EventName        string                             `json:"eventName"`
	ErrorCode        string                             `json:"errorCode"`
	ErrorMessage     string                             `json:"errorMessage"`
	ResponseElements AWSCloudFrontDetailResponseElement `json:"responseElements"`
}

type AWSCloudFrontDetailResponseElement struct {
	Distribution struct {
		ID                 string `json:"id"`
		DomainName         string `json:"domainName"`
		Status             string `json:"status"`
		DistributionConfig struct {
			Origins struct {
				Items []struct {
					DomainName string `json:"domainName"`
					ID         string `json:"id"`
				} `json:"items"`
			} `json:"origins"`
		} `json:"distributionConfig"`
	} `json:"distribution"`
}

func (cf *AWSCloudFrontDistributionResource) RefreshState() error {
	return nil
}

func (cf *AWSCloudFrontDistributionResource) SendNotification() error {
	return nil
}

func (cf *AWSCloudFrontDistributionResource) GetType() string {
	return SERVICE_AWS_CLOUDFRONT
}

func (cf *AWSCloudFrontDistributionResource) GetMetadata() map[string]interface{} {
	return map[string]interface{}{
		"account":         cf.AccountID,
		"domain":          cf.DomainName,
		"distribution-id": cf.DistributionID,
		"event":           cf.EventName,
		"serviceType":     cf.GetType(),
	}
}

func (cf *AWSCloudFrontDistributionResource) GetLogger() *log.Logger {
	return cf.logger
}

func (cf *AWSCloudFrontDistributionResource) createDistributionEntries() error {
	db, err := graph.NewDBConnection()
	defer db.Close()
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}

	// get account
	account := model.Account{AccountID: cf.AccountID}
	err = db.FirstOrCreate(&account, account).Error
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("account: %#v", account)

	distro := model.Distribution{DistributionID: cf.DistributionID, Domain: cf.DomainName, AccountID: account.ID}
	err = db.FirstOrCreate(&distro, distro).Error
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("distro: %#v", distro)

	if distro.Domain != cf.DomainName {
		cf.GetLogger().WithFields(cf.GetMetadata()).Debugf("saving cloudfront distro: %#v", distro)
		distro.Domain = cf.DomainName
		err = db.Save(&distro).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}
	}

	//write origins
	for _, cfOrigin := range cf.Origins {
		origin := model.Origin{
			OriginID:       cfOrigin.ID,
			Domain:         cfOrigin.Domain,
			DistributionID: distro.ID,
		}

		err = db.FirstOrCreate(&origin, origin).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}

		cf.logger.WithFields(cf.GetMetadata()).Debugf("origin: %#v", origin)

	}
	return nil
}

func (cf *AWSCloudFrontDistributionResource) updateDistributionEntries() error {
	db, err := graph.NewDBConnection()
	defer db.Close()
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}

	// get account
	account := model.Account{AccountID: cf.AccountID}
	err = db.FirstOrCreate(&account, account).Error
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("account: %#v", account)

	distro := model.Distribution{DistributionID: cf.DistributionID, Domain: cf.DomainName, AccountID: account.ID}
	err = db.FirstOrCreate(&distro, distro).Error
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("distro: %#v", distro)

	if distro.Domain != cf.DomainName {
		cf.GetLogger().WithFields(cf.GetMetadata()).Debugf("saving cloudfront distro: %#v", distro)
		distro.Domain = cf.DomainName
		err = db.Model(&model.Distribution{}).Save(&distro).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}
	}

	// get all current origins
	var currentOrigins []model.Origin
	err = db.Find(&currentOrigins, model.Origin{DistributionID: distro.ID}).Error
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}

	currentOriginsMap := map[string]model.Origin{}
	for _, origin := range currentOrigins {
		currentOriginsMap[origin.OriginID] = origin
	}

	updateOriginsMap := map[string]model.Origin{}
	for _, origin := range cf.Origins {
		updateOriginsMap[origin.ID] = model.Origin{
			DistributionID: distro.ID,
			OriginID:       origin.ID,
			Domain:         origin.Domain,
		}
	}

	// origins to remove
	removeOrigins := []model.Origin{}
	// origins to add
	addOrigns := []model.Origin{}

	for originID, origin := range updateOriginsMap {
		if _, ok := currentOriginsMap[originID]; ok {
			// update origin is already in db/graph
		} else {
			// need to add origin as its not in graph
			addOrigns = append(addOrigns, origin)
		}
	}

	for originID, origin := range currentOriginsMap {
		if _, ok := updateOriginsMap[originID]; ok {
			// origin in graph is in update
		} else {
			// origin in graph is not in update
			removeOrigins = append(removeOrigins, origin)
		}
	}

	for _, origin := range addOrigns {
		err := db.FirstOrCreate(&origin, origin).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}
	}

	for _, origin := range removeOrigins {
		err := db.Delete(&origin).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}
	}
	return nil
}

type AWSCloudFrontDistributionHijackableResource struct {
	AWSCloudFrontDistributionResource
}

func (cf *AWSCloudFrontDistributionHijackableResource) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passedInMetadata map[string]interface{}) error {
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
	logger := instrument.GetInstrumentedLogger(opts, ctx)
	cf.logger = logger

	var cfDetails AWSCloudFrontDetail
	err = json.Unmarshal(event.Detail, &cfDetails)
	if err != nil {
		cf.logger.Error(err.Error(), nil)
		return err
	}

	if cfDetails.ErrorCode != "" {
		return errors.New(cfDetails.ErrorMessage)
	}

	if reflect.DeepEqual(cfDetails.ResponseElements, (AWSCloudFrontDetailResponseElement{})) {
		return errors.New("response element of cloudfront distribution is missing")
	}
	cf.AccountID = event.AccountID
	cf.DistributionID = cfDetails.ResponseElements.Distribution.ID
	cf.DomainName = cfDetails.ResponseElements.Distribution.DomainName
	cf.EventName = cfDetails.EventName

	origins := make([]AWSCloudFrontOrigin, len(cfDetails.ResponseElements.Distribution.DistributionConfig.Origins.Items))

	for idx, origin := range cfDetails.ResponseElements.Distribution.DistributionConfig.Origins.Items {
		origins[idx] = AWSCloudFrontOrigin{
			ID:     origin.ID,
			Domain: origin.DomainName,
		}
	}
	cf.Origins = origins

	return nil
}

func (cf *AWSCloudFrontDistributionHijackableResource) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
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
	cf.logger = instrument.GetInstrumentedLogger(opts, ctx)
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		cf.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "json marshal error",
		}).WithFields(cf.GetMetadata()).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-route53-record-set resource")
	}

	err = json.Unmarshal(structJson, cf)
	if err != nil {
		cf.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-route53-record-set",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).WithFields(cf.GetMetadata()).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-route53-record-set resource")
	}

	return nil
}

func (cf *AWSCloudFrontDistributionHijackableResource) PublishState() error {
	cf.logger.WithFields(cf.GetMetadata()).Debug("publishing cloudfront distribution")
	switch cf.EventName {
	case "CreateDistribution":
		return cf.createDistributionEntries()
	case "UpdateDistribution":
		return cf.updateDistributionEntries()
	default:
		cf.logger.WithFields(cf.GetMetadata()).Debugf("cloudfront distribution event %v unknown", cf.EventName)
	}

	return nil
}
