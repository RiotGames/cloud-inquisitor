package newrelic

import (
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/google/uuid"
	"github.com/newrelic/go-agent/v3/integrations/nrlambda"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/newrelic/go-agent/v3/newrelic"
)

// StartNewRelicLambda is a wrapper around the New Relic provided Lambda integration
//  It will add a custom logger and set it to the New Relic App logger
//  This logger will also log certain metadata to include:
//    - lambda-uuid: a uuid designted to the lamda instance (multiple executions can use same instance)
func StartNewRelicLambda(handler interface{}, name string) {
	lambdaUUID, _ := uuid.NewRandom()
	opts := log.LoggerOpts{
		Level: log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: map[string]interface{}{
			"cloud-inquisitor-lambda-uuid": lambdaUUID.String(),
		},
	}
	app, err := newrelic.NewApplication(
		newrelic.ConfigAppName(name),
		nrlambda.ConfigOption(),
		//nrlogrus.ConfigStandardLogger(),
		LamdbaExecutionLogger(opts),
	)
	if err != nil {
		panic(err.Error())
	}
	nrlambda.Start(handler, app)
}
