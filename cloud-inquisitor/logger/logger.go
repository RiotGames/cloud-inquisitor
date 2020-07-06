package logger

import (
	"context"

	"github.com/sirupsen/logrus"
)

type Logger struct {
	opts LoggerOpts
	L    *logrus.Logger
}

type LoggerOpts struct {
	Level    logrus.Level
	Metadata logrus.Fields
	Context  context.Context
}

func NewLogger(opts LoggerOpts) *Logger {
	logger := &Logger{L: logrus.New(), opts: opts}
	logger.L.SetLevel(opts.Level)
	return logger
}

func (logger *Logger) SetFormatter(formatter logrus.Formatter) {
	logger.L.SetFormatter(formatter)
}

func (logger *Logger) AddMetadataField(key string, value interface{}) {
	newOps := logger.opts
	newOps.Metadata[key] = value
	logger.opts = newOps
}

func (logger *Logger) GetMetadata() map[string]interface{} {
	return logger.opts.Metadata
}

func (logger *Logger) WithFields(fields logrus.Fields) *logrus.Entry {
	// add custom fields here
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	if logger.opts.Context != nil {
		return logger.L.WithContext(logger.opts.Context).WithFields(fields)
	}

	return logger.L.WithFields(fields)
}

func (logger *Logger) WithContext(ctx context.Context) *logrus.Entry {
	// add metadata
	fields := logrus.Fields{}
	for key, value := range logger.opts.Metadata {
		fields[key] = value
	}

	if logger.opts.Context != nil {
		return logger.L.WithContext(logger.opts.Context).WithFields(fields).WithContext(ctx)
	}

	return logger.L.WithFields(fields).WithContext(ctx)
}

func (logger *Logger) Debug(msg string, context map[string]interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	if context != nil {
		for key, value := range context {
			fields[key] = value
		}
	}

	entry := logger.L.WithFields(fields)
	entry.Debug(msg)
}

func (logger *Logger) Debugf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.L.WithFields(fields)
	entry.Debugf(fmt, args...)
}

func (logger *Logger) DebugEnabled() bool {
	lvl := logger.L.GetLevel()
	return lvl >= logrus.DebugLevel
}

func (logger *Logger) Info(msg string, context map[string]interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	if context != nil {
		for key, value := range context {
			fields[key] = value
		}
	}

	entry := logger.L.WithFields(fields)
	entry.Info(msg)
}
func (logger *Logger) Infof(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.L.WithFields(fields)
	entry.Infof(fmt, args...)
}

func (logger *Logger) Warn(msg string, context map[string]interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	if context != nil {
		for key, value := range context {
			fields[key] = value
		}
	}

	entry := logger.L.WithFields(fields)
	entry.Warn(msg)
}
func (logger *Logger) Warnf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.L.WithFields(fields)
	entry.Warnf(fmt, args...)
}

func (logger *Logger) Error(msg string, context map[string]interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	if context != nil {
		for key, value := range context {
			fields[key] = value
		}
	}

	entry := logger.L.WithFields(fields)
	entry.Error(msg)
}

func (logger *Logger) Errorf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.L.WithFields(fields)
	entry.Errorf(fmt, args...)
}

func (logger *Logger) Fatal(msg string, context map[string]interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	if context != nil {
		for key, value := range context {
			fields[key] = value
		}
	}

	entry := logger.L.WithFields(fields)
	entry.Fatal(msg)
}

func (logger *Logger) Fatalf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.L.WithFields(fields)
	entry.Fatalf(fmt, args...)
}

// defaults to info level
func LogrusLevelConv(level string) logrus.Level {
	switch level {
	case "debug", "Debug", "DEBUG":
		return logrus.DebugLevel
	case "info", "Info", "INFO":
		return logrus.InfoLevel
	case "warn", "warning", "Warn", "Warning", "WARN", "WARNING":
		return logrus.WarnLevel
	case "error", "Error", "ERROR":
		return logrus.ErrorLevel
	case "fatal", "Fatal", "FATAL":
		return logrus.FatalLevel
	default:
		return logrus.InfoLevel
	}
}
