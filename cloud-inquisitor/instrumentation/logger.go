package instrument

import (
	"context"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation/newrelic"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

func GetInstrumentedLogger(opts logger.LoggerOpts, ctx context.Context) *logger.Logger {
	if settings.GetBool("newrelic.logging.enabled") {
		switch settings.GetString("newrelic.logging.provider") {
		case "lambda":
			return newrelic.NewLambdaLogger(opts, ctx)
		case "api":
			hookOpts := newrelic.DefaultNewRelicHookOpts
			hookOpts.License = settings.GetString("newrelic.license")
			hookOpts.ApplicationName = settings.GetString("name")

			hookLogger := logger.NewLogger(opts)
			hookLogger.L.AddHook(newrelic.NewNewRelicHook(hookOpts))
			return hookLogger
		}
	}

	defaultLogger := logger.NewLogger(opts)
	defaultLogger.Warn("Default logger as no logger definition was found", nil)

	return defaultLogger
}
