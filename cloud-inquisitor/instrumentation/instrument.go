package instrument

type Instrumentor interface {
	//GetLogger(opts logger.LoggerOpts, context context.Context) *logger.Logger
	StartLambda(handler interface{}, lambdaName string)
}
