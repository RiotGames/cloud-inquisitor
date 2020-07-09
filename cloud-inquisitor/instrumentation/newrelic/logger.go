package newrelic

import (
	"context"

	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/newrelic/go-agent/v3/integrations/logcontext/nrlogrusplugin"
	"github.com/newrelic/go-agent/v3/newrelic"
	//"github.com/sirupsen/logrus"
)

func LamdbaExecutionLogger(opts log.LoggerOpts) newrelic.ConfigOption {
	logger := log.NewLogger(opts)
	logger.L.SetFormatter(nrlogrusplugin.ContextFormatter{})
	return newrelic.ConfigLogger(logger)
}

func NewLambdaLogger(opts log.LoggerOpts, passedContext context.Context) *log.Logger {
	nrLogger := log.NewLogger(opts)
	nrLogger.L.SetFormatter(nrlogrusplugin.ContextFormatter{})
	optsWithContext := opts
	var loggerContext context.Context = nil

	txn := GetTxnFromLambdaContext(passedContext, nrLogger)
	if txn != nil {
		loggerContext = NewContextFromTxn(txn, nrLogger)
	} else {
		nrLogger.Warn("unable to parse new relic transaction", nil)
		optsWithContext.Metadata["new-relic-txn"] = false
	}

	optsWithContext.Context = loggerContext
	nrLogger = log.NewLogger(optsWithContext)
	nrLogger.L.SetFormatter(nrlogrusplugin.ContextFormatter{})

	return nrLogger
}
