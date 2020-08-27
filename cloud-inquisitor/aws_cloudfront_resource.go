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
	OriginGroups   []AWSCloudFrontOriginGroup
	logger         *log.Logger
}

type AWSCloudFrontOrigin struct {
	ID     string
	Domain string
}

type AWSCloudFrontOriginGroup struct {
	ID      string
	Domains []string
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
			OriginGroups struct {
				Items []struct {
					ID      string `json:"id"`
					Members struct {
						Items []struct {
							OriginID string `json:"originId"`
						} `json:"items"`
					} `json:"members"`
				} `json:"items"`
			} `json:"originGroups"`
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

	//write origin groups
	for _, cfGroup := range cf.OriginGroups {
		group := model.OriginGroup{
			GroupID:        cfGroup.ID,
			DistributionID: distro.ID,
		}

		err = db.FirstOrCreate(&group, group).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}

		cf.logger.WithFields(cf.GetMetadata()).Debugf("origin group: %#v", group)

		for _, groupDomain := range cfGroup.Domains {
			domain := model.Value{
				ValueID:       groupDomain,
				OriginGroupID: group.ID,
			}

			err = db.FirstOrCreate(&domain, domain).Error
			if err != nil {
				cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
				return err
			}

			cf.logger.WithFields(cf.GetMetadata()).Debugf("origin group domain: %#v", domain)
		}
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
	cf.logger.WithFields(cf.GetMetadata()).Debugf("origins: %#v", currentOrigins)

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
	cf.logger.WithFields(cf.GetMetadata()).Debugf("origins to add: %#v", addOrigns)

	for originID, origin := range currentOriginsMap {
		if _, ok := updateOriginsMap[originID]; ok {
			// origin in graph is in update
		} else {
			// origin in graph is not in update
			removeOrigins = append(removeOrigins, origin)
		}
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("origins to remove: %#v", removeOrigins)

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

	//get all current origin groups
	var currentOriginGroups []model.OriginGroup
	err = db.Model(model.OriginGroup{}).Preload("Origins").Find(&currentOriginGroups, model.OriginGroup{DistributionID: distro.ID}).Error
	if err != nil {
		cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
		return err
	}

	currentOriginGroupMap := map[string]model.OriginGroup{}
	for _, group := range currentOriginGroups {
		currentOriginGroupMap[group.GroupID] = group
	}
	updateOriginGroupMap := map[string]model.OriginGroup{}
	for _, group := range cf.OriginGroups {

		groupModel := model.OriginGroup{
			DistributionID: distro.ID,
			GroupID:        group.ID,
			Origins:        make([]model.Value, len(group.Domains)),
		}

		for idx, domain := range group.Domains {
			groupModel.Origins[idx] = model.Value{
				ValueID: domain,
			}
		}

		updateOriginGroupMap[group.ID] = groupModel

	}

	removeOriginGroups := []model.OriginGroup{}
	addOriginGroups := []model.OriginGroup{}

	for groupID, group := range updateOriginGroupMap {
		if _, ok := currentOriginGroupMap[groupID]; ok {
			// group already in graph
		} else {
			addOriginGroups = append(addOriginGroups, group)
		}
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("origin groups to add: %#v", addOriginGroups)

	for groupID, group := range currentOriginGroupMap {
		if _, ok := updateOriginGroupMap[groupID]; ok {
			// group is still in graph
		} else {
			//group has been removed
			removeOriginGroups = append(removeOriginGroups, group)
		}
	}
	cf.logger.WithFields(cf.GetMetadata()).Debugf("origin groups to remove: %#v", removeOriginGroups)

	for _, group := range addOriginGroups {
		groupModel := model.OriginGroup{
			DistributionID: distro.ID,
			GroupID:        group.GroupID,
		}
		err = db.FirstOrCreate(&groupModel, groupModel).Error
		if err != nil {
			cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
			return err
		}

		for _, origin := range group.Origins {
			originVal := model.Value{
				ValueID:       origin.ValueID,
				OriginGroupID: groupModel.ID,
			}

			err = db.FirstOrCreate(&originVal, originVal).Error
			if err != nil {
				cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
				return err
			}
		}
	}

	for _, group := range removeOriginGroups {
		for _, value := range group.Origins {
			err = db.Delete(&value).Error
			if err != nil {
				cf.logger.WithFields(cf.GetMetadata()).Error(err.Error())
				return err
			}
		}

		err = db.Delete(&group).Error
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

	cf.logger.WithFields(cf.GetMetadata()).Debugf("aws event detail response elements: %#v", cfDetails.ResponseElements)

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

	groups := make([]AWSCloudFrontOriginGroup, len(cfDetails.ResponseElements.Distribution.DistributionConfig.OriginGroups.Items))
	for idx, group := range cfDetails.ResponseElements.Distribution.DistributionConfig.OriginGroups.Items {
		groups[idx] = AWSCloudFrontOriginGroup{
			ID: group.ID,
		}

		domains := make([]string, len(group.Members.Items))
		for dIdx, domain := range group.Members.Items {
			domains[dIdx] = domain.OriginID
		}

		groups[idx].Domains = domains
	}

	cf.OriginGroups = groups

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
