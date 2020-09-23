package graph

// This file will be automatically regenerated based on the schema, any resolver implementations
// will be copied through when generating and any unknown code will be moved to the end.

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/generated"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	log "github.com/sirupsen/logrus"
)

func (r *accountResolver) Zones(ctx context.Context, obj *model.Account) ([]*model.Zone, error) {
	log.Infof("account <%v> getting zones\n", obj.AccountID)
	log.Debugf("%#v\n", *obj)

	account := model.Account{AccountID: obj.AccountID}
	err := r.DB.Where(&account).First(&account).Error
	if err != nil {
		return []*model.Zone{}, err
	}
	var zones []*model.Zone
	err = r.DB.Model(&account).Association("ZoneRelation").Find(&zones).Error
	if err != nil {
		return []*model.Zone{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, zone := range zones {
			log.Debugf("%v: account <%#v> zones <%#v>\n", idx, obj.AccountID, *zone)
		}
	}

	return zones, nil
}

func (r *accountResolver) Zone(ctx context.Context, obj *model.Account, id string) (*model.Zone, error) {
	log.Infof("account %v getting zone %v\n", obj.AccountID, id)
	zone := model.Zone{ZoneID: id}
	err := r.DB.Model(obj).Related(&zone, "ZoneRelation").Error
	if err != nil {
		log.Error(err.Error())
		return nil, err
	}

	log.Debugf("for account %v found zone %v\n", obj.AccountID, zone)

	return &zone, nil
}

func (r *accountResolver) Records(ctx context.Context, obj *model.Account) ([]*model.Record, error) {
	log.Infof("account <%v> getting records\n", obj.AccountID)
	log.Debugf("%#v\n", *obj)
	account := model.Account{AccountID: obj.AccountID}
	err := r.DB.Where(&account).First(&account).Error
	if err != nil {
		return []*model.Record{}, nil
	}

	var records []*model.Record
	err = r.DB.Model(&account).Association("RecordRelation").Find(&records).Error
	if err != nil {
		return []*model.Record{}, nil
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, record := range records {
			log.Debugf("%v: account %v record %#v\n", idx, account.AccountID, *record)
		}
	}

	return records, nil
}

func (r *accountResolver) Distributions(ctx context.Context, obj *model.Account) ([]*model.Distribution, error) {
	log.Infof("account <%v> getting cloudfront distributions\n", obj.AccountID)
	log.Debugf("%#v\n", *obj)
	account := model.Account{AccountID: obj.AccountID}
	err := r.DB.Where(&account).First(&account).Error
	if err != nil {
		return []*model.Distribution{}, nil
	}

	var distributions []*model.Distribution
	err = r.DB.Model(&account).Association("DistributionRelation").Find(&distributions).Error
	if err != nil {
		return []*model.Distribution{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, distro := range distributions {
			log.Debugf("%v: account %v record %#v\n", idx, account.AccountID, *distro)
		}
	}

	return distributions, nil
}

func (r *distributionResolver) Origins(ctx context.Context, obj *model.Distribution) ([]*model.Origin, error) {
	log.Debugf("getting all origins for distribution %v\v", obj.DistributionID)
	distro := model.Distribution{DistributionID: obj.DistributionID}
	err := r.DB.Model(&model.Distribution{}).Where(&distro).First(&distro).Error
	if err != nil {
		return []*model.Origin{}, err
	}

	var origins []*model.Origin
	err = r.DB.Model(&distro).Association("OriginRelation").Find(&origins).Error
	if err != nil {
		return []*model.Origin{}, err
	}

	return origins, nil
}

func (r *distributionResolver) OriginGroups(ctx context.Context, obj *model.Distribution) ([]*model.OriginGroup, error) {
	log.Debugf("getting all origin groups for distribution: %s", obj.DistributionID)
	var originGroups []*model.OriginGroup
	err := r.DB.Preload("Origins").Find(&originGroups, model.OriginGroup{DistributionID: obj.ID}).Error
	if err != nil {
		return []*model.OriginGroup{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, group := range originGroups {
			log.Debugf("%v: origin group %#v\n", idx, *group)
		}
	}

	return originGroups, nil
}

func (r *queryResolver) Accounts(ctx context.Context) ([]*model.Account, error) {
	log.Debug("getting all accounts")
	var accounts []*model.Account
	err := r.DB.Find(&accounts).Error
	if err != nil {
		return []*model.Account{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, account := range accounts {
			log.Debugf("%v: account %#v\n", idx, *account)
		}
	}
	return accounts, nil
}

func (r *queryResolver) Account(ctx context.Context, id string) (*model.Account, error) {
	log.Infof("looking up account by id <%s>\n", id)
	var account model.Account
	err := r.DB.Where(&model.Account{AccountID: id}).First(&account).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("found account <%#v>\n", account)
	}

	return &account, nil
}

func (r *queryResolver) Zones(ctx context.Context) ([]*model.Zone, error) {
	log.Debug("getting all zones")
	var zones []*model.Zone
	err := r.DB.Find(&zones).Error
	if err != nil {
		return []*model.Zone{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for zidx, zone := range zones {
			log.Debugf("%v: zone %#v\n", zidx, *zone)
		}
	}

	return zones, nil
}

func (r *queryResolver) Zone(ctx context.Context, id string) (*model.Zone, error) {
	log.Infof("getting zone by id >%s>\n", id)
	var zone model.Zone
	err := r.DB.Where(&model.Zone{ZoneID: id}).First(&zone).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("zone <%#v>\n", zone)
	}

	return &zone, nil
}

func (r *queryResolver) Records(ctx context.Context) ([]*model.Record, error) {
	log.Debug("getting all records")
	var records []*model.Record
	err := r.DB.Find(&records).Error
	if err != nil {
		return []*model.Record{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for ridx, record := range records {
			log.Debugf("%v: record <%#v>\n", ridx, *record)
		}
	}

	return records, nil
}

func (r *queryResolver) Record(ctx context.Context, id string) (*model.Record, error) {
	log.Infof("getting record by id <%s>\n", id)
	var record model.Record
	err := r.DB.Where(&model.Record{RecordID: id}).First(&record).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("record <%#v>\n", record)
	}

	return &record, nil
}

func (r *queryResolver) PointedAtByRecords(ctx context.Context, domain string) ([]*model.Record, error) {
	log.Infof("finding all records that point to %v", domain)
	var recordValues []*model.Value
	err := r.DB.Where(model.Value{ValueID: domain}).Find(&recordValues).Error
	if err != nil {
		return []*model.Record{}, err
	}

	recordIds := []uint{}
	for _, val := range recordValues {
		if val.RecordID != 0 {
			recordIds = append(recordIds, val.RecordID)
		}
	}

	var records []*model.Record
	err = r.DB.Find(&records, recordIds).Error
	if err != nil {
		return []*model.Record{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for _, record := range records {
			log.Debugf("record %#v points to domain %v", record, domain)
		}
	}

	return records, nil
}

func (r *queryResolver) Values(ctx context.Context) ([]*model.Value, error) {
	log.Info("getting all values")
	var values []*model.Value
	err := r.DB.Find(&values).Error
	if err != nil {
		return []*model.Value{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, val := range values {
			log.Debugf("%v: record <%#v>\n", idx, *val)
		}
	}

	return values, nil
}

func (r *queryResolver) Value(ctx context.Context, id string) (*model.Value, error) {
	log.Infof("getting value by id <%s>\n", id)
	var value model.Value
	err := r.DB.Where(&model.Value{ValueID: id}).First(&value).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("value <%#v>\n", value)
	}

	return &value, nil
}

func (r *queryResolver) Distributions(ctx context.Context) ([]*model.Distribution, error) {
	log.Info("getting all distributions")
	var distributions []*model.Distribution
	err := r.DB.Find(&distributions).Error
	if err != nil {
		return []*model.Distribution{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, distro := range distributions {
			log.Debugf("%v: cloudfront distro <%#v>\n", idx, *distro)
		}
	}

	return distributions, nil
}

func (r *queryResolver) Distribution(ctx context.Context, id string) (*model.Distribution, error) {
	log.Debugf("getting distribution with id: %v\n", id)
	distro := model.Distribution{DistributionID: id}
	err := r.DB.First(&distro, distro).Error
	if err != nil {
		return &model.Distribution{}, err
	}

	return &distro, nil
}

func (r *queryResolver) PointedAtByDistribution(ctx context.Context, domain string) ([]*model.Distribution, error) {
	log.Infof("finding all distributions pointing at domain %v", domain)
	distroIds := []uint{}
	origins, err := r.PointedAtByOrigin(ctx, domain)
	if err != nil {
		log.Errorf("erroring getting origins for distribution: %v", err.Error())
	} else {
		for _, origin := range origins {
			distroIds = append(distroIds, origin.DistributionID)
		}
	}

	originGroups, err := r.PointedAtByOriginGroup(ctx, domain)
	if err != nil {
		log.Errorf("error getting origin groups for distribution: %v", err.Error())
	} else {
		for _, origin := range originGroups {
			distroIds = append(distroIds, origin.DistributionID)
		}
	}

	var distributions []*model.Distribution
	err = r.DB.Find(&distributions, distroIds).Error
	if err != nil {
		return []*model.Distribution{}, nil
	}

	if log.GetLevel() == log.DebugLevel {
		for _, distro := range distributions {
			log.Debugf("found distribution %v for domain %v", *distro, domain)
		}
	}

	return distributions, nil
}

func (r *queryResolver) Origins(ctx context.Context) ([]*model.Origin, error) {
	log.Debugln("getting all origins")
	var origins []*model.Origin
	err := r.DB.Model(&model.Origin{}).Find(&origins).Error
	if err != nil {
		return []*model.Origin{}, err
	}

	return origins, nil
}

func (r *queryResolver) Origin(ctx context.Context, id string) (*model.Origin, error) {
	log.Debugf("getting origin with id: %v\n", id)

	origin := model.Origin{OriginID: id}
	err := r.DB.First(&origin, origin).Error
	if err != nil {
		return &model.Origin{}, err
	}

	return &origin, nil
}

func (r *queryResolver) PointedAtByOrigin(ctx context.Context, domain string) ([]*model.Origin, error) {
	log.Infof("looking for all origins pointing at dominan %v", domain)
	var origins []*model.Origin
	err := r.DB.Where(model.Origin{Domain: domain}).Find(&origins).Error
	if err != nil {
		return []*model.Origin{}, err
	}

	return origins, nil
}

func (r *queryResolver) OriginGroups(ctx context.Context) ([]*model.OriginGroup, error) {
	var originGroups []*model.OriginGroup
	err := r.DB.Preload("Origins").Find(&originGroups).Error
	if err != nil {
		return []*model.OriginGroup{}, err
	}

	return originGroups, nil
}

func (r *queryResolver) PointedAtByOriginGroup(ctx context.Context, domain string) ([]*model.OriginGroup, error) {
	log.Infof("looking for origin groups pointing at domain %v", domain)

	var domainValues []*model.Value
	err := r.DB.Where(model.Value{ValueID: domain}).Find(&domainValues).Error
	if err != nil {
		return []*model.OriginGroup{}, err
	}

	originGroupIds := []uint{}
	for _, val := range domainValues {
		originGroupIds = append(originGroupIds, val.OriginGroupID)
	}

	var originGroups []*model.OriginGroup
	err = r.DB.Find(&originGroups, originGroupIds).Error
	if err != nil {
		return []*model.OriginGroup{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for _, group := range originGroups {
			log.Debugf("origin group %v pointing to domain %v", group, domain)
		}
	}

	return originGroups, nil
}

func (r *queryResolver) ElasticbeanstalkEnvironments(ctx context.Context) ([]*model.ElasticbeanstalkEnvironment, error) {
	log.Debug("getting all elasticbeanstalk environments")
	var environments []*model.ElasticbeanstalkEnvironment
	err := r.DB.Find(&environments).Error
	if err != nil {
		log.Errorf("error getting all elasticbeanstalk environments: %v", err.Error())
		return []*model.ElasticbeanstalkEnvironment{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for _, env := range environments {
			log.Debugf("got elasticbeanstalk environment: %#v", *env)
		}
	}

	return environments, nil
}

func (r *queryResolver) ElasticbeanstalkByEndpoint(ctx context.Context, endpoint string) (*model.ElasticbeanstalkEnvironment, error) {
	log.Debugf("getting elasticbeanstalk by domain: %v", endpoint)
	var beanstalk model.ElasticbeanstalkEnvironment
	err := r.DB.Find(&beanstalk, model.ElasticbeanstalkEnvironment{
		CName: endpoint,
	}).Error

	if err == nil {
		return &beanstalk, err
	}

	err = r.DB.Find(&beanstalk, model.ElasticbeanstalkEnvironment{
		EnvironmentURL: endpoint,
	}).Error

	return &beanstalk, err
}

func (r *queryResolver) GetCloudFrontUpstreamHijack(ctx context.Context, domains []string) ([]*model.HijackableResource, error) {
	hijackChain := []*model.HijackableResource{}

	// 1. check origins
	for _, domain := range domains {
		origins, err := r.Query().PointedAtByOrigin(ctx, domain)
		if err != nil {
			log.Errorf("error looking up domain %s", domain)
			continue
		}

		for _, origin := range origins {
			completeOrigin, err := r.Query().Origin(ctx, origin.OriginID)
			if err != nil {
				log.Errorf("error looking up origin with id %v", origin.OriginID)
				continue
			}

			var account model.Account
			err = r.DB.First(&account, origin.OriginID).Error
			if err != nil {
				log.Errorf("unable to get account for origin %#v", *completeOrigin)
				continue
			}
			hijackChain = append(hijackChain, &model.HijackableResource{
				ID:      completeOrigin.OriginID,
				Type:    model.TypeDistribution,
				Account: account.AccountID,
				Value: &model.Value{
					ValueID: completeOrigin.Domain,
				},
			})
		}
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("found hijack chain for endpoints: %#v", domains)
		for idx, chainElement := range hijackChain {
			log.Debugf("%v: %#v", idx, *chainElement)
		}
	}

	return hijackChain, nil
}

func (r *queryResolver) GetElasticbeanstalkUpstreamHijack(ctx context.Context, endpoints []string) ([]*model.HijackableResource, error) {
	// elasticbeanstalks are endpoints are only fronted by other resources
	hijackChain := []*model.HijackableResource{}
	searchEndpoints := endpoints
	// need to check:
	// 1. cloudfront
	for _, endpoint := range searchEndpoints {
		distributions, err := r.Query().PointedAtByDistribution(ctx, endpoint)
		if err != nil {
			log.Errorf("error looking up distributions for endpoint %v", endpoint)
			continue
		}

		for _, distro := range distributions {
			completeDistro, err := r.Query().Distribution(ctx, distro.DistributionID)
			if err != nil {
				log.Errorf("error looking up distribution with id %v", distro.DistributionID)
				continue
			}

			var account model.Account
			err = r.DB.First(&account, completeDistro.AccountID).Error
			if err != nil {
				log.Errorf("unable to get account for distribution %#v", *completeDistro)
				continue
			}

			hijackChain = append(hijackChain, &model.HijackableResource{
				ID:      completeDistro.DistributionID,
				Type:    model.TypeDistribution,
				Account: account.AccountID,
				Value: &model.Value{
					ValueID: completeDistro.Domain,
				},
			})
		}
	}

	if log.GetLevel() == log.DebugLevel {
		for _, resource := range hijackChain {
			log.Debugf("resource: %#v", *resource)
		}
	}

	for _, resource := range hijackChain {
		searchEndpoints = append(searchEndpoints, resource.Value.ValueID)
	}
	// 2. route53
	for _, endpoint := range searchEndpoints {
		records, err := r.Query().PointedAtByRecords(ctx, endpoint)
		if err != nil {
			log.Errorf("unable to get records taht point to endpoint %v", endpoint)
			continue
		}

		for _, record := range records {
			completeRecord, err := r.Query().Record(ctx, record.RecordID)
			if err != nil {
				log.Errorf("unable to get complete record for record id %v", record.RecordID)
				continue
			}

			var account model.Account
			err = r.DB.First(&account, completeRecord.AccountID).Error
			if err != nil {
				log.Errorf("unable to get account for distribution %#v", *completeRecord)
				continue
			}

			hijackChain = append(hijackChain, &model.HijackableResource{
				ID:      completeRecord.RecordID,
				Type:    model.TypeRecord,
				Account: account.AccountID,
				Value: &model.Value{
					ValueID: completeRecord.RecordID,
				},
			})

		}
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("found hijack chain for domains: %#v", endpoints)
		for idx, chainElement := range hijackChain {
			log.Debugf("%v: %#v", idx, *chainElement)
		}
	}

	return hijackChain, nil
}

func (r *queryResolver) HijackChainByDomain(ctx context.Context, id string, domains []string, typeArg model.Type) (*model.HijackableResourceChain, error) {
	switch typeArg {
	case model.TypeDistribution:
		cf, err := r.Query().Distribution(ctx, id)
		if err != nil {
			log.Errorf("error getting cloudfront: %v", err.Error())
			return nil, err
		}

		var account *model.Account = nil
		err = r.DB.Find(account, cf.AccountID).Error
		if err != nil {
			log.Errorf("unable to find account for cloudfront distribution: %#v", *cf)
			return nil, err
		}

		chain, err := r.Query().GetCloudFrontUpstreamHijack(ctx, domains)
		if err != nil {
			log.Errorf("recieved error when querying for cloudfront distribution hijacks: %v", err.Error())
			return nil, err
		}

		return &model.HijackableResourceChain{
			ID: id,
			Resource: &model.HijackableResource{
				ID:      id,
				Account: account.AccountID,
				Type:    model.TypeElasticbeanstalk,
				Value: &model.Value{
					ValueID: cf.Domain,
				},
			},
			Upstream:   chain,
			Downstream: []*model.HijackableResource{},
		}, err

	case model.TypeElasticbeanstalk:
		/*
			ID      string `json:"id"`
			Account string `json:"account"`
			Type    Type   `json:"type"`
			Value   *Value `json:"value"`
		*/
		beanstalk, err := r.Query().ElasticbeanstalkByEndpoint(ctx, domains[0])
		if err != nil {
			log.Errorf("error getting beanstalk: %v", err.Error())
			return nil, err
		}

		var account *model.Account = nil
		err = r.DB.Find(account, beanstalk.AccountID).Error
		if err != nil {
			log.Errorf("unable to find account for beanstalk: %#v", *beanstalk)
			return nil, err
		}

		chain, err := r.Query().GetElasticbeanstalkUpstreamHijack(ctx, domains)
		if err != nil {
			log.Errorf("recieved error when querying for elastic beanstalk hijacks: %v", err.Error())
			return nil, err
		}

		return &model.HijackableResourceChain{
			ID: id,
			Resource: &model.HijackableResource{
				ID:      id,
				Account: account.AccountID,
				Type:    model.TypeElasticbeanstalk,
				Value: &model.Value{
					ValueID: beanstalk.CName,
				},
			},
			Upstream:   chain,
			Downstream: []*model.HijackableResource{},
		}, err
	}

	return &model.HijackableResourceChain{}, nil
}

func (r *recordResolver) Values(ctx context.Context, obj *model.Record) ([]*model.Value, error) {
	log.Infof("record <%v> getting values\n", obj.RecordID)
	log.Debugf("%#v\n", *obj)

	record := model.Record{RecordID: obj.RecordID}
	err := r.DB.Where(&record).First(&record).Error
	if err != nil {
		return []*model.Value{}, err
	}
	var values []*model.Value
	err = r.DB.Model(&record).Association("ValueRelation").Find(&values).Error
	if err != nil {
		return []*model.Value{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, value := range values {
			log.Debugf("%v: record <%#v> value <%#v>\n", idx, obj.RecordID, *value)
		}
	}

	return values, nil
}

func (r *zoneResolver) Records(ctx context.Context, obj *model.Zone) ([]*model.Record, error) {
	log.Infof("zone <%v> getting records\n", obj.ZoneID)
	log.Debugf("%#v\n", *obj)

	records := []*model.Record{}
	err := r.DB.Model(obj).Related(&records, "RecordRelation").Error
	if err != nil {
		log.Error(err.Error())
		return []*model.Record{}, nil
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, record := range records {
			log.Debugf("%v: zone <%#v> record <%#v>\n", idx, obj.ZoneID, *record)
		}
	}

	return records, nil
}

func (r *zoneResolver) Record(ctx context.Context, obj *model.Zone, id string) (*model.Record, error) {
	log.Infof("for xzone %v getting record %v\n", obj.ZoneID, id)
	record := model.Record{RecordID: id}
	err := r.DB.Model(obj).Related(&record, "RecordRelation").Error
	if err != nil {
		return nil, err
	}

	log.Debugf("for zone %v got record %#v\n", obj.ZoneID, record)

	return &record, nil
}

// Account returns generated.AccountResolver implementation.
func (r *Resolver) Account() generated.AccountResolver { return &accountResolver{r} }

// Distribution returns generated.DistributionResolver implementation.
func (r *Resolver) Distribution() generated.DistributionResolver { return &distributionResolver{r} }

// Query returns generated.QueryResolver implementation.
func (r *Resolver) Query() generated.QueryResolver { return &queryResolver{r} }

// Record returns generated.RecordResolver implementation.
func (r *Resolver) Record() generated.RecordResolver { return &recordResolver{r} }

// Zone returns generated.ZoneResolver implementation.
func (r *Resolver) Zone() generated.ZoneResolver { return &zoneResolver{r} }

type accountResolver struct{ *Resolver }
type distributionResolver struct{ *Resolver }
type queryResolver struct{ *Resolver }
type recordResolver struct{ *Resolver }
type zoneResolver struct{ *Resolver }
