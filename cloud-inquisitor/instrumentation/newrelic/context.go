package newrelic

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/newrelic/go-agent/v3/newrelic"
	"github.com/sirupsen/logrus"
)

func GetTxnFromLambdaContext(ctx context.Context, logger *logger.Logger) *newrelic.Transaction {
	if txn := newrelic.FromContext(ctx); txn != nil {
		logger.WithFields(logrus.Fields{}).Debug("generated new relic transaction from lambda context")
		return txn
	}
	logger.WithFields(logrus.Fields{}).Warn("unable to generate  new relic transaction from lambda context")
	return nil
}

func NewContextFromTxn(txn *newrelic.Transaction, logger *logger.Logger) context.Context {
	ctx := newrelic.NewContext(context.Background(), txn)
	logger.WithContext(ctx).WithFields(logrus.Fields{}).Debug("generated context from new relic transaction")
	return ctx
}
