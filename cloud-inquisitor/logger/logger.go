package logger

import (
	"context"

	"github.com/sirupsen/logrus"
)

type Logger struct {
	opts LoggerOpts
	l    *logrus.Logger
}

type LoggerOpts struct {
	Level    logrus.Level
	Metadata map[string]interface{}
}

func NewLogger(opts LoggerOpts) *Logger {
	logger := &Logger{l: logrus.New(), opts: opts}
	logger.l.SetLevel(opts.Level)
	return logger
}

func (logger *Logger) SetFormatter(formatter logrus.Formatter) {
	logger.l.SetFormatter(formatter)
}

func (logger *Logger) WithFields(fields logrus.Fields) *logrus.Entry {
	// add custom fields here
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	return logger.l.WithFields(fields)
}

func (logger *Logger) WithContext(ctx context.Context) *logrus.Entry {
	// add metadata
	fields := logrus.Fields{}
	for key, value := range logger.opts.Metadata {
		fields[key] = value
	}

	return logger.WithFields(fields).WithContext(ctx)
}

func (logger *Logger) Debug(args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Debug(args...)
}

func (logger *Logger) Debugf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Debugf(fmt, args...)
}

func (logger *Logger) Info(args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Info(args...)
}
func (logger *Logger) Infof(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Infof(fmt, args...)
}

func (logger *Logger) Warn(args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Warn(args...)
}
func (logger *Logger) Warnf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Warnf(fmt, args...)
}

func (logger *Logger) Error(args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Error(args...)
}

func (logger *Logger) Errorf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Errorf(fmt, args...)
}

func (logger *Logger) Fatal(args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Fatal(args...)
}

func (logger *Logger) Fatalf(fmt string, args ...interface{}) {
	fields := logrus.Fields{}
	for uuidName, uuid := range logger.opts.Metadata {
		fields[uuidName] = uuid
	}

	entry := logger.l.WithFields(fields)
	entry.Fatalf(fmt, args...)
}
