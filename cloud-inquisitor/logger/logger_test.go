package logger

import (
	"context"
	"testing"

	"github.com/newrelic/go-agent/v3/integrations/logcontext/nrlogrusplugin"
	"github.com/newrelic/go-agent/v3/newrelic"
	"github.com/sirupsen/logrus"
)

func TestLogger(t *testing.T) {
	opts := LoggerOpts{
		Level: LogrusLevelConv("debug"),
		Metadata: map[string]interface{}{
			"test": "test",
		},
	}
	log := NewLogger(opts)
	log.Info("test1", nil)
	log.WithFields(logrus.Fields{"field": "one"}).Warn("next test")
}

func TestContextFormatLogger(t *testing.T) {
	opts := LoggerOpts{
		Level: LogrusLevelConv("debug"),
		Metadata: map[string]interface{}{
			"test": "test",
		},
	}
	log := NewLogger(opts)
	log.L.SetFormatter(nrlogrusplugin.ContextFormatter{})
	log.Info("test1", nil)
	log.WithFields(logrus.Fields{"field": "one"}).Warn("next test")
}

func TestContextFormatNewRelicContextLogger(t *testing.T) {
	opts := LoggerOpts{
		Level: LogrusLevelConv("debug"),
		Metadata: map[string]interface{}{
			"test": "test",
		},
	}
	log := NewLogger(opts)
	log.L.SetFormatter(nrlogrusplugin.ContextFormatter{})
	ctx := newrelic.NewContext(context.Background(), nil)
	log.Info("test1", nil)
	log.WithFields(logrus.Fields{"field": "one"}).Warn("next test")
	log.WithContext(ctx).WithField("context-added", "true").Error("with context")
}
