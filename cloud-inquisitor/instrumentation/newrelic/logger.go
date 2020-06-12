package newrelic

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"

	"github.com/newrelic/go-agent/v3/integrations/logcontext/nrlogrusplugin"
)

// following NR docs at https://docs.newrelic.com/docs/logs/enable-logs/logs-context-go/configure-logs-context-go
func NewLambdaLogger(opts logger.LoggerOpts) *logger.Logger {
	nrLogger := logger.NewLogger(opts)
	nrLogger.SetFormatter(nrlogrusplugin.ContextFormatter{})
	nrLogger.Info("New logger created for use with New Relic")
	return nrLogger
}
