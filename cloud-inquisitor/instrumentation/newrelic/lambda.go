package newrelic

import (
	"github.com/newrelic/go-agent/_integrations/nrlambda"
	"github.com/newrelic/go-agent/v3/newrelic"
)

func StartNewRelicLambda(handler interface{}) {
	app, err := newrelic.NewApplication(
		nrlambda.NewConfig(),
		newrelic.ConfigDistributedTracerEnabled(true),
	)
	if err != nil {
		log.Fatal(err.Error())
	}
	m.app = app
	nrlambda.Start(hander, app)
}
