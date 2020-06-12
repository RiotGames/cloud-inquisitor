package newrelic

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	newrelic "github.com/newrelic/go-agent"
	"github.com/sirupsen/logrus"
)

func GetTxnFromLambdaContext(ctx context.Context, logger *logger.Logger) *newrelic.Transaction {
	if txn := newrelic.FromContext(ctx); txn != nil {
		logger.WithFields(logrus.Fields{}).Info("Able to generate txn for NewRelic from Lambda Context")
	}
	logger.WithFields(logrus.Fields{}).Warn("Unable to generate txn for NewRelic from Lambda Context")
	return nil
}

func NewContextFromTxn(txn *newrelic.Transaction, logger *logger.Logger) context.Context {
	ctx := newrelic.NewContext(context.Background(), *txn)
	logger.WithContext(ctx).WithFields(logrus.Fields{}).Info("New context for New Relic from Transaction(txn) has been generated")
	return ctx
}
