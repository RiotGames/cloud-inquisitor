package newrelic

import (
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/google/uuid"
	"github.com/newrelic/go-agent/v3/integrations/nrlambda"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/newrelic/go-agent/v3/newrelic"
)

func StartNewRelicLambda(handler interface{}, name string) {
	var lambdaUUID interface{}
	lambdaUUID, _ = uuid.NewRandom()
	opts := log.LoggerOpts{
		Level: log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: map[string]interface{}{
			"lambda-uuid": lambdaUUID,
		},
	}
	app, err := newrelic.NewApplication(
		newrelic.ConfigAppName(name),
		nrlambda.ConfigOption(),
		//nrlogrus.ConfigStandardLogger(),
		LamdbaLogger(opts),
	)
	if err != nil {
		panic(err.Error())
	}
	nrlambda.Start(handler, app)
}
