package graph

// This file will not be regenerated automatically.
//
// It serves as dependency injection for your app, add any dependencies you require here.

import (
	"time"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/database"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
)

type Resolver struct {
	DB *gorm.DB
}

func NewResolver() (*Resolver, error) {
	db, err := database.NewDBConnection()
	if err != nil {
		db.Close()
		return nil, err
	}
	// SetMaxIdleConns sets the maximum number of connections in the idle connection pool.
	db.DB().SetMaxIdleConns(10)

	// SetMaxOpenConns sets the maximum number of open connections to the database.
	db.DB().SetMaxOpenConns(100)

	// SetConnMaxLifetime sets the maximum amount of time a connection may be reused.
	db.DB().SetConnMaxLifetime(time.Hour)

	return &Resolver{DB: db}, nil
}

func (r *Resolver) Close() error {
	return r.DB.Close()
}
