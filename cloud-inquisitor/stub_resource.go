package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"

	instrument "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-lambda-go/events"
)

type StubResource struct {
	State  int
	logger *log.Logger
}

func (t *StubResource) Audit() (Action, error) {
	var result Action

	switch t.State {
	case 0, 1, 2:
		result = ACTION_NOTIFY
	case 3:
		result = ACTION_PREVENT
	case 4:
		result = ACTION_REMOVE
	}

	t.State += 1

	return result, nil
}

func (t *StubResource) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passedInMetadata map[string]interface{}) error {
	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: passedInMetadata,
	}
	t.logger = instrument.GetInstrumentedLogger(opts, ctx)

	t.logger.Debug("creating new stub resource", nil)

	t.State = 0
	return nil
}

func (t *StubResource) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: passedInMetadata,
	}
	t.logger = instrument.GetInstrumentedLogger(opts, ctx)

	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		t.logger.Error(err.Error(), nil)
		return errors.New("unable to marshal stub resoruce")
	}

	err = json.Unmarshal(structJson, t)
	if err != nil {
		t.logger.Error(err.Error(), nil)
		return errors.New("unable to unmarshal stub resoruce")
	}

	return nil
}

func (t *StubResource) PublishState() error {
	t.logger.Debugf("PublishState: %#v\n", *t)
	return nil
}

func (t *StubResource) RefreshState() error {
	return nil
}

func (t *StubResource) SendLogs() error {
	return nil
}

func (t *StubResource) SendMetrics() error {
	return nil
}

func (t *StubResource) SendNotification() error {
	t.logger.Debugf("Notification send: %#v\n", *t)
	return nil
}

func (t *StubResource) TakeAction(a Action) error {
	t.logger.Debugf("taking action %#v on resource: %#v\n", a, *t)
	return nil
}

func (t *StubResource) GetType() Service {
	return SERVICE_STUB
}

func (t *StubResource) GetMetadata() map[string]interface{} {
	return map[string]interface{}{}
}

func (t *StubResource) GetLogger() *log.Logger {
	return t.logger
}

func (t *StubResource) GetMissingTags() []string {
	return []string{}
}

func (t *StubResource) GetTags() map[string]string {
	return map[string]string{}
}

func (t *StubResource) AnalyzeForHijack() (HijackChain, error) {
	return HijackChain{[]HijackChainElement{}}, nil
}
