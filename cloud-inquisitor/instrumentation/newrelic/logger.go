package newrelic

import (
	"context"

	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/newrelic/go-agent/v3/integrations/logcontext/nrlogrusplugin"
	"github.com/newrelic/go-agent/v3/newrelic"
	"github.com/sirupsen/logrus"
)

func LamdbaLogger(opts log.LoggerOpts) newrelic.ConfigOption {
	logger := log.NewLogger(opts)
	logger.L.SetFormatter(nrlogrusplugin.ContextFormatter{})
	return newrelic.ConfigLogger(logger)
}

func ApplicationLogger(opts log.LoggerOpts, passedContext context.Context) *logrus.Entry {
	nrLogger := log.NewLogger(opts)
	nrLogger.L.SetFormatter(nrlogrusplugin.ContextFormatter{})
	txn := GetTxnFromLambdaContext(passedContext, nrLogger)
	if txn != nil {
		ctx := NewContextFromTxn(txn, nrLogger)
		return nrLogger.WithContext(ctx)
	} else {
		nrLogger.Warn("unable to parse new relic transaction", nil)
		return nrLogger.WithFields(logrus.Fields{"new-relic-txn": false})
	}

}
