package graph

// This file will be automatically regenerated based on the schema, any resolver implementations
// will be copied through when generating and any unknown code will be moved to the end.

import (
	"context"
	"fmt"

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

func (r *distributionResolver) GetOriginsWithDomain(ctx context.Context, obj *model.Distribution, domain string) ([]*model.Origin, error) {
	log.Debugf("getting all origins with domain %v for distribution %v", domain, obj.DistributionID)

	var origins []*model.Origin
	err := r.DB.Where(model.Origin{DistributionID: obj.ID, Domain: domain}).Find(&origins).Error
	if err != nil {
		log.Errorf("error finding origin with domain %v for distribution %v: %v", domain, obj.DistributionID, err.Error())
		return []*model.Origin{}, err
	}

	return origins, nil
}

func (r *distributionResolver) GetOriginGroupsWithDomain(ctx context.Context, obj *model.Distribution, domain string) ([]*model.OriginGroup, error) {
	log.Debugf("getting all origin groups with domain %v for distribution %v", domain, obj.DistributionID)

	originGroupsWithDomain := []*model.OriginGroup{}
	originGroups, err := r.OriginGroups(ctx, obj)
	if err != nil {
		return originGroupsWithDomain, err
	}

	for _, originGroup := range originGroups {
		localResolver := originGroupResolver{r.Resolver}
		values, valueErr := localResolver.GetValueWithDomain(ctx, originGroup, domain)
		if valueErr != nil {
			log.Errorf("error getting value for origin group %v and domain %v: %v", originGroup.GroupID, domain, err.Error())
		}
		if len(values) > 0 {
			appendGroup := originGroup
			appendGroup.Origins = make([]model.Value, len(values))
			for valIdx, value := range values {
				appendGroup.Origins[valIdx] = *value
			}

			originGroupsWithDomain = append(originGroupsWithDomain, appendGroup)
		}
	}

	return originGroupsWithDomain, nil
}

func (r *distributionResolver) ConvertToHijackableResourceMap(ctx context.Context, obj *model.Distribution) (*model.HijackableResourceMap, error) {
	panic(fmt.Errorf("not implemented"))
}

func (r *elasticbeanstalkEnvironmentResolver) ConvertToHijackableResourceMap(ctx context.Context, obj *model.ElasticbeanstalkEnvironment) (*model.HijackableResourceMap, error) {
	panic(fmt.Errorf("not implemented"))
}

func (r *originGroupResolver) GetValueWithDomain(ctx context.Context, obj *model.OriginGroup, domain string) ([]*model.Value, error) {
	panic(fmt.Errorf("not implemented"))
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

func (r *queryResolver) GetAccountWithAccountID(ctx context.Context, accountID string) (*model.Account, error) {
	log.Infof("looking up account by id <%s>\n", accountID)
	var account model.Account
	err := r.DB.Where(&model.Account{AccountID: accountID}).First(&account).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("found account <%#v>\n", account)
	}

	return &account, nil
}

func (r *queryResolver) GetAccountWithDomain(ctx context.Context, domain string) (*model.Account, error) {
	panic(fmt.Errorf("not implemented"))
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

func (r *queryResolver) GetZoneWithResourceID(ctx context.Context, resourceID string) (*model.Zone, error) {
	log.Infof("getting zone by id >%s>\n", resourceID)
	var zone model.Zone
	err := r.DB.Where(&model.Zone{ZoneID: resourceID}).First(&zone).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("zone <%#v>\n", zone)
	}

	return &zone, nil
}

func (r *queryResolver) GetAllZonesWithDomain(ctx context.Context, domain string) ([]*model.Zone, error) {
	panic(fmt.Errorf("not implemented"))
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

func (r *queryResolver) GetRecordWithResourceID(ctx context.Context, resourceID string) (*model.Record, error) {
	log.Infof("getting record by id: %s\n", resourceID)
	var record model.Record
	err := r.DB.Where(&model.Record{RecordID: resourceID}).First(&record).Error
	if err != nil {
		return nil, err
	}

	if log.GetLevel() == log.DebugLevel {
		log.Debugf("record <%#v>\n", record)
	}

	return &record, nil
}

func (r *queryResolver) GetAllRecordsWithDomain(ctx context.Context, domain string) ([]*model.Record, error) {
	panic(fmt.Errorf("not implemented"))
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

func (r *queryResolver) GetAllValueWithValueID(ctx context.Context, valueID string) (*model.Value, error) {
	log.Infof("getting value by id: %s\n", valueID)
	var value model.Value
	err := r.DB.Where(&model.Value{ValueID: valueID}).First(&value).Error
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

func (r *queryResolver) GetDistributionWithResourceID(ctx context.Context, resourceID string) (*model.Distribution, error) {
	log.Debugf("getting distribution with id: %v\n", resourceID)
	distro := model.Distribution{DistributionID: resourceID}
	err := r.DB.First(&distro, distro).Error
	if err != nil {
		return &model.Distribution{}, err
	}

	return &distro, nil
}

func (r *queryResolver) GetAllDistributionsWithDomain(ctx context.Context, domain string) ([]*model.Distribution, error) {
	log.Infof("finding all distributions pointing at domain %v", domain)
	distros, err := r.Distributions(ctx)
	if err != nil {
		return []*model.Distribution{}, err
	}

	distrosWithDomain := []*model.Distribution{}
	for _, distro := range distros {
		distroResolver := distributionResolver{r.Resolver}
		appendDistro := distro
		shouldAppend := false
		origins, originErr := distroResolver.GetOriginsWithDomain(ctx, distro, domain)
		if originErr != nil {
			log.Errorf("error getting origins for distribution %v with domain %v: %v", distro.DistributionID, domain, err.Error())
		} else {
			if len(origins) > 0 {
				appendDistro.OriginRelation = make([]model.Origin, len(origins))
				for originIdx, origin := range origins {
					appendDistro.OriginRelation[originIdx] = *origin
				}
				shouldAppend = true
			}
		}
		groups, groupErr := distroResolver.GetOriginGroupsWithDomain(ctx, distro, domain)
		if groupErr != nil {
			log.Errorf("error getting origin groups for distribution %v with domain %v: %v", distro.DistributionID, domain, err.Error())
		} else {
			if len(groups) > 0 {
				appendDistro.OriginGroupRelation = make([]model.OriginGroup, len(groups))
				for gIdx, group := range groups {
					appendDistro.OriginGroupRelation[gIdx] = *group
				}
				shouldAppend = true
			}
		}

		if shouldAppend {
			distrosWithDomain = append(distrosWithDomain, appendDistro)
		}

	}

	return distrosWithDomain, nil
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

func (r *queryResolver) GetOriginWithResourceID(ctx context.Context, resourceID string) (*model.Origin, error) {
	log.Debugf("getting origin with id: %v\n", resourceID)

	origin := model.Origin{OriginID: resourceID}
	err := r.DB.First(&origin, origin).Error
	if err != nil {
		return &model.Origin{}, err
	}

	return &origin, nil
}

func (r *queryResolver) GetAllOriginsWithDomain(ctx context.Context, domain string) ([]*model.Origin, error) {
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

func (r *queryResolver) GetOriginGroupWithResourceID(ctx context.Context, resourceID string) (*model.OriginGroup, error) {
	panic(fmt.Errorf("not implemented"))
}

func (r *queryResolver) GetAllOriginGroupsWithDomain(ctx context.Context, domain string) ([]*model.OriginGroup, error) {
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

func (r *queryResolver) GetElasticbeanstalkWithResourceID(ctx context.Context, resourceID string) (*model.ElasticbeanstalkEnvironment, error) {
	panic(fmt.Errorf("not implemented"))
}

func (r *queryResolver) GetAllElasticbeanstalksWithDomain(ctx context.Context, domain string) ([]*model.ElasticbeanstalkEnvironment, error) {
	log.Debugf("getting elasticbeanstalk by domain: %v", domain)
	var beanstalks []*model.ElasticbeanstalkEnvironment
	err := r.DB.Find(&beanstalks, model.ElasticbeanstalkEnvironment{
		CName: domain,
	}).Error

	if err == nil {
		return beanstalks, err
	}

	err = r.DB.Find(&beanstalks, model.ElasticbeanstalkEnvironment{
		EnvironmentURL: domain,
	}).Error

	return beanstalks, err
}

func (r *queryResolver) GetHijackMapWithResourceIDAndDomainsAndTypeAndDirection(ctx context.Context, queryLabel string, resourceID string, domains []string, typeArg model.Type, direction model.Direction) (*model.HijackableResourceRoot, error) {
	switch typeArg {
	case model.TypeElasticbeanstalk:
		/*
			ID      string `json:"id"`
			Account string `json:"account"`
			Type    Type   `json:"type"`
			Value   *Value `json:"value"`
		*/
		beanstalk, err := r.Query().GetElasticbeanstalkWithResourceID(ctx, resourceID)
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

		switch direction {
		case model.DirectionUpstream:
			//elastic beastalk has 2 endpoints, the env url and CNAME
			// env url
			hijackRoot := &model.HijackableResourceRoot{
				ID:             queryLabel,
				RootResourceID: resourceID,
				Direction:      direction,
				Maps:           []*model.HijackableResourceMap{},
			}

			// get cloudfront distributions for the beanstalk URL
			distros, err := r.GetAllDistributionsWithDomain(ctx, beanstalk.EnvironmentURL)
			if err != nil {
				log.Errorf("error getting cloudfront distribiutions for resource %v and domain %v: %v", resourceID, beanstalk.EnvironmentURL, err.Error())
			} else {
				for _, distro := range distros {
					distroresolver := distributionResolver{r.Resolver}
					distroMap, convertErr := distroresolver.ConvertToHijackableResourceMap(ctx, distro)
					if convertErr != nil {
						log.Errorf("error converting distribution %v to hijackable resource map: %v", distro.DistributionID, err.Error())
					} else {
						hijackRoot.Maps = append(hijackRoot.Maps, distroMap)
					}
				}
			}

			// get cloudfront distributions for the beanstalk cname
			distros, err = r.GetAllDistributionsWithDomain(ctx, beanstalk.CName)
			if err != nil {
				log.Errorf("error getting cloudfront distribiutions for resource %v and domain %v: %v", resourceID, beanstalk.CName, err.Error())
			} else {
				for _, distro := range distros {
					distroresolver := distributionResolver{r.Resolver}
					distroMap, convertErr := distroresolver.ConvertToHijackableResourceMap(ctx, distro)
					if convertErr != nil {
						log.Errorf("error converting distribution %v to hijackable resource map: %v", distro.DistributionID, err.Error())
					} else {
						hijackRoot.Maps = append(hijackRoot.Maps, distroMap)
					}
				}
			}

			// get zones with records that point to beanstalk url
			zones, err := r.GetAllZonesWithDomain(ctx, beanstalk.EnvironmentURL)
			if err != nil {
				log.Errorf("error getting route53 zones for resource %v and domain %v: %v", resourceID, beanstalk.EnvironmentURL, err.Error())
			} else {
				for _, zone := range zones {
					zResolver := zoneResolver{r.Resolver}
					zoneMap, convertErr := zResolver.ConvertToHijackableResourceMap(ctx, zone)
					if convertErr != nil {
						log.Errorf("error converting zone %v to hijackable resource map: %v", zone.ZoneID, err.Error())
					} else {
						hijackRoot.Maps = append(hijackRoot.Maps, zoneMap)
					}
				}
			}
			// get zones with records that point to beanstalk cname
			zones, err = r.GetAllZonesWithDomain(ctx, beanstalk.CName)
			if err != nil {
				log.Errorf("error getting route53 zones for resource %v and domain %v: %v", resourceID, beanstalk.CName, err.Error())
			} else {
				for _, zone := range zones {
					zResolver := zoneResolver{r.Resolver}
					zoneMap, convertErr := zResolver.ConvertToHijackableResourceMap(ctx, zone)
					if convertErr != nil {
						log.Errorf("error converting zone %v to hijackable resource map: %v", zone.ZoneID, err.Error())
					} else {
						hijackRoot.Maps = append(hijackRoot.Maps, zoneMap)
					}
				}
			}

			return hijackRoot, nil

		case model.DirectionDownstream:
			// there are no resource downsteam of a elasticbeanstalk
			return &model.HijackableResourceRoot{
				ID:             queryLabel,
				RootResourceID: resourceID,
				Direction:      direction,
				Maps:           []*model.HijackableResourceMap{},
			}, nil

		default:
			log.Error("unkown direction provided")
			return nil, fmt.Errorf("unknown hijack direction given resourceID: %v", resourceID)
		}
	case model.TypeDistribution:
		distro, err := r.GetDistributionWithResourceID(ctx, resourceID)
		if err != nil {
			log.Errorf("error getting cloudfront distribution with id %v: %v", resourceID, err.Error())
			return nil, err
		}

		var account model.Account
		err = r.DB.First(&account, distro.AccountID).Error
		if err != nil {
			log.Errorf("error getting account for distribution %v: %v", distro.DistributionID, err.Error())
			return nil, err
		}

		hijackRoot := &model.HijackableResourceRoot{
			ID:             queryLabel,
			RootResourceID: resourceID,
			Direction:      direction,
			Maps:           []*model.HijackableResourceMap{},
		}

		switch direction {
		case model.DirectionDownstream:
			// downsteam can be s3 buckets, elasticbeanstalks, route53/zones(?)
			distroDomains := []string{}
			distroResolver := distributionResolver{r.Resolver}
			origins, originErr := distroResolver.Origins(ctx, distro)
			if originErr != nil {
				log.Errorf("error looking up origins for cloudfront distribution %v: %v", distro.DistributionID, originErr.Error())
			} else {
				for _, origin := range origins {
					distroDomains = append(distroDomains, origin.Domain)
				}
			}

			groups, groupError := distroResolver.OriginGroups(ctx, distro)
			if groupError != nil {
				log.Errorf("error looking up origins for cloudfront distribution %v: %v", distro.DistributionID, groupError.Error())
			} else {
				for _, group := range groups {
					for _, val := range group.Origins {
						distroDomains = append(distroDomains, val.ValueID)
					}
				}
			}

			for _, domain := range distroDomains {
				//check for beanstalks
				beanstalks, beastnstalkErr := r.GetAllElasticbeanstalksWithDomain(ctx, domain)
				if beastnstalkErr != nil {
					log.Errorf("error getting elastickbeans with domain %v: %V", domain, err.Error())
				} else {
					for _, beanstalk := range beanstalks {
						beanstalkResolver := elasticbeanstalkEnvironmentResolver{r.Resolver}
						beanstalkMap, convertError := beanstalkResolver.ConvertToHijackableResourceMap(ctx, beanstalk)
						if convertError != nil {
							log.Errorf("error converting elasticbeanstalk %v to map format: %v", beanstalk.EnvironmentID)
						} else {
							hijackRoot.Maps = append(hijackRoot.Maps, beanstalkMap)
						}
					}
				}

				//check against s3 buckets
			}

		case model.DirectionUpstream:
			upstreamDomain := distro.Domain
			// upstream can be route53/zones
			zones, zoneErr := r.GetAllZonesWithDomain(ctx, upstreamDomain)
			if zoneErr != nil {
				log.Errorf("error getting zones with domain %v: %v", upstreamDomain, err.Error())
			} else {
				for _, zone := range zones {
					zresolver := zoneResolver{r.Resolver}
					zoneMap, convertError := zresolver.ConvertToHijackableResourceMap(ctx, zone)
					if convertError != nil {
						log.Errorf("error converting zone %v to map format: %v", zone.ZoneID, err.Error())
					} else {
						hijackRoot.Maps = append(hijackRoot.Maps, zoneMap)
					}
				}
			}

			// use domain list to search for all possible
		}

		return hijackRoot, nil
	}

	return nil, nil
}

func (r *queryResolver) GetHijackMapWithResourceIDAndDomainsAndTypeAndDirectionThenFlattened(ctx context.Context, queryLabel string, resourceID string, domains []string, typeArg model.Type, direction model.Direction) (*model.HijackableResourceRoot, error) {
	originalRoot, err := r.GetHijackMapWithResourceIDAndDomainsAndTypeAndDirection(ctx, queryLabel, resourceID, domains, typeArg, direction)
	if err != nil {
		log.Errorf("error getting domain hijack map: %v", err.Error())
		return nil, err
	}

	hijackMaps := []*model.HijackableResourceMap{}
	for _, hijackMap := range originalRoot.Maps {
		mapsToProcess := []struct {
			list []model.HijackableResourceMap
		}{
			{
				list: []model.HijackableResourceMap{*hijackMap},
			},
		}

		for len(mapsToProcess) > 0 {
			// pop map
			currentSet := mapsToProcess[0]

			// remove popped map
			switch len(mapsToProcess) {
			case 1:
				mapsToProcess = []struct {
					list []model.HijackableResourceMap
				}{}
			default:
				mapsToProcess[0] = mapsToProcess[len(mapsToProcess)-1]
				mapsToProcess = mapsToProcess[:len(mapsToProcess)-1]
			}
			// end of map queue processing

			lastMap := currentSet.list[len(currentSet.list)-1]
			switch len(lastMap.Contains) {
			case 0:
				// no more things to process in this list of maps
				// take list of maps and turn into nested contains
				var rootMap *model.HijackableResourceMap
				for idx := range currentSet.list {
					reverseIdx := len(currentSet.list) - 1 - idx
					switch reverseIdx {
					case len(currentSet.list) - 1:
						rootMap = &model.HijackableResourceMap{
							Resource:  currentSet.list[reverseIdx].Resource,
							Contains:  []*model.HijackableResourceMap{},
							Direction: originalRoot.Direction,
						}
					default:
						rootMap = &model.HijackableResourceMap{
							Resource:  currentSet.list[reverseIdx].Resource,
							Contains:  []*model.HijackableResourceMap{rootMap},
							Direction: originalRoot.Direction,
						}
					}
				}
				hijackMaps = append(hijackMaps, rootMap)
			case 1:
				// one node to follow
				currentSet.list = append(currentSet.list, *lastMap.Contains[0])
				mapsToProcess = append(mapsToProcess, currentSet)
			default:
				// many nodes to follow
				for _, setElement := range lastMap.Contains {
					newSet := struct {
						list []model.HijackableResourceMap
					}{
						list: append(currentSet.list, *setElement),
					}

					mapsToProcess = append(mapsToProcess, newSet)
				}
			}
		}
	}

	originalRoot.Maps = hijackMaps
	return originalRoot, nil
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

func (r *recordResolver) GetValuesWithDomain(ctx context.Context, obj *model.Record, domain string) ([]*model.Value, error) {
	panic(fmt.Errorf("not implemented"))
}

func (r *recordResolver) ConvertToHijackableResourceMap(ctx context.Context, obj *model.Record) (*model.HijackableResourceMap, error) {
	panic(fmt.Errorf("not implemented"))
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

func (r *zoneResolver) GetRecordsWithDomain(ctx context.Context, obj *model.Zone, domain string) ([]*model.Record, error) {
	log.Debugf("looking for all zones with domain %v in zone %v", domain, obj.ZoneID)
	var records []*model.Record
	err := r.DB.Where(model.Record{ZoneID: obj.ID}).Find(&records).Error
	if err != nil {
		log.Errorf("error finding all records for zone %v: %v", obj.ZoneID, err.Error())
		return nil, err
	}

	returnRecords := []*model.Record{}
	for _, record := range records {
		recResolver := recordResolver{r.Resolver}
		values, valueErr := recResolver.GetValuesWithDomain(ctx, record, domain)
		if valueErr != nil {
			log.Errorf("unable to get values with domain %v in record %v in zone %v: %v", domain, record.RecordID, obj.ZoneID, err.Error())
		} else {
			record.ValueRelation = make([]model.Value, len(values))
			for idx, val := range values {
				record.ValueRelation[idx] = *val
			}
			returnRecords = append(returnRecords, record)
		}
	}

	return returnRecords, nil
}

func (r *zoneResolver) ConvertToHijackableResourceMap(ctx context.Context, obj *model.Zone) (*model.HijackableResourceMap, error) {
	panic(fmt.Errorf("not implemented"))
}

// Account returns generated.AccountResolver implementation.
func (r *Resolver) Account() generated.AccountResolver { return &accountResolver{r} }

// Distribution returns generated.DistributionResolver implementation.
func (r *Resolver) Distribution() generated.DistributionResolver { return &distributionResolver{r} }

// ElasticbeanstalkEnvironment returns generated.ElasticbeanstalkEnvironmentResolver implementation.
func (r *Resolver) ElasticbeanstalkEnvironment() generated.ElasticbeanstalkEnvironmentResolver {
	return &elasticbeanstalkEnvironmentResolver{r}
}

// OriginGroup returns generated.OriginGroupResolver implementation.
func (r *Resolver) OriginGroup() generated.OriginGroupResolver { return &originGroupResolver{r} }

// Query returns generated.QueryResolver implementation.
func (r *Resolver) Query() generated.QueryResolver { return &queryResolver{r} }

// Record returns generated.RecordResolver implementation.
func (r *Resolver) Record() generated.RecordResolver { return &recordResolver{r} }

// Zone returns generated.ZoneResolver implementation.
func (r *Resolver) Zone() generated.ZoneResolver { return &zoneResolver{r} }

type accountResolver struct{ *Resolver }
type distributionResolver struct{ *Resolver }
type elasticbeanstalkEnvironmentResolver struct{ *Resolver }
type originGroupResolver struct{ *Resolver }
type queryResolver struct{ *Resolver }
type recordResolver struct{ *Resolver }
type zoneResolver struct{ *Resolver }
