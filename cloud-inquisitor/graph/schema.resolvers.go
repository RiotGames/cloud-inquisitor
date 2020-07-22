package graph

// This file will be automatically regenerated based on the schema, any resolver implementations
// will be copied through when generating and any unknown code will be moved to the end.

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/generated"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	log "github.com/sirupsen/logrus"
)

func (r *queryResolver) Accounts(ctx context.Context) ([]*model.Account, error) {
	log.Debug("getting all accounts")
	var accounts []*model.Account
	err := r.DB.Set("gorm:auto_preload", true).Find(&accounts).Error
	if err != nil {
		return []*model.Account{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, account := range accounts {
			log.Debugf("account %v: <id: %v>\n", idx, account.ID)
			for zidx, zone := range account.Zones {
				log.Debugf("\tzone %v: <id:%v, name: %v>\n", zidx, zone.ID, zone.Name)
			}
		}
	}
	return accounts, nil
}

func (r *queryResolver) Account(ctx context.Context, id string) (*model.Account, error) {
	var account model.Account
	err := r.DB.Where(&model.Account{AccountID: id}).Set("gorm:auto_preload", true).First(&account).Error
	if err != nil {
		return nil, err
	}

	return &account, nil
}

func (r *queryResolver) Zones(ctx context.Context) ([]*model.Zone, error) {
	log.Debug("getting all zones")
	var zones []*model.Zone
	err := r.DB.Set("gorm:auto_preload", true).Find(&zones).Error
	if err != nil {
		return []*model.Zone{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for zidx, zone := range zones {
			log.Debugf("zone %v: <id:%v, name: %v>\n", zidx, zone.ZoneID, zone.Name)
		}
	}

	return zones, nil
}

func (r *queryResolver) Zone(ctx context.Context, id string) (*model.Zone, error) {
	var zone model.Zone
	err := r.DB.Where(&model.Zone{ZoneID: id}).Set("gorm:auto_preload", true).First(&zone).Error
	if err != nil {
		return nil, err
	}

	return &zone, nil
}

func (r *queryResolver) Records(ctx context.Context) ([]*model.Record, error) {
	log.Debug("getting all records")
	var records []*model.Record
	err := r.DB.Set("gorm:auto_preload", true).Find(&records).Error
	if err != nil {
		return []*model.Record{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for ridx, record := range records {
			log.Debugf("record %v: <id:%v, type: %v>\n", ridx, record.RecordID, record.RecordType)
		}
	}

	return records, nil
}

func (r *queryResolver) Record(ctx context.Context, id string) (*model.Record, error) {
	var record model.Record
	err := r.DB.Set("gorm:auto_preload", true).Where(&model.Record{RecordID: id}).First(&record).Error
	if err != nil {
		return nil, err
	}

	return &record, nil
}

// Query returns generated.QueryResolver implementation.
func (r *Resolver) Query() generated.QueryResolver { return &queryResolver{r} }

type queryResolver struct{ *Resolver }
