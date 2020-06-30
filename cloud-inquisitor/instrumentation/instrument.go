package instrument

import (
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
)

type Instrumentor interface {
	GetLogger(opts logger.LoggerOpts) *logger.Logger
	StartLambda(handler interface{}, lambdaName string)
}
