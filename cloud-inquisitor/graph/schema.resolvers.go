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

	db, err := NewDBConnection()
	if err != nil {
		return []*model.Zone{}, err
	}

	account := model.Account{AccountID: obj.AccountID}
	err = db.Where(&account).First(&account).Error
	if err != nil {
		return []*model.Zone{}, err
	}
	var zones []*model.Zone
	err = db.Model(&account).Association("ZoneRelation").Find(&zones).Error
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

func (r *queryResolver) HijackChainByDomain(ctx context.Context, domain string) (*model.HijackableResourceChain, error) {
	panic(fmt.Errorf("not implemented"))
}

func (r *queryResolver) GetElasticbeanstalkUpstreamHijack(ctx context.Context, endpoints []string) ([]*model.HijackableResource, error) {
	panic(fmt.Errorf("not implemented"))
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
