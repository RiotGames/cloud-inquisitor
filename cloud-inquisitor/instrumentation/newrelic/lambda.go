package newrelic

import (
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/newrelic/go-agent/v3/integrations/nrlambda"
	"github.com/newrelic/go-agent/v3/newrelic"
	"github.com/sirupsen/logrus"
)

func StartNewRelicLambda(handler interface{}) {
	logger := NewLambdaLogger(log.LoggerOpts{Level: logrus.InfoLevel})
	app, err := newrelic.NewApplication(
		nrlambda.ConfigOption(),
		newrelic.ConfigDistributedTracerEnabled(true),
	)
	if err != nil {
		logger.Fatal("Unable to create New Relic application")
	}
	nrlambda.Start(handler, app)
}
