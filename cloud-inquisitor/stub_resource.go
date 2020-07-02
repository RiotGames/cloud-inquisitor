package cloudinquisitor

import (
	"encoding/json"
	"errors"

	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/aws/aws-lambda-go/events"
)

type StubResource struct {
	State int
}

func (t *StubResource) Audit(logger *log.Logger) (Action, error) {
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

func (t *StubResource) NewFromEventBus(event events.CloudWatchEvent, logger *log.Logger) error {
	t.State = 0
	return nil
}

func (t *StubResource) NewFromPassableResource(resource PassableResource, logger *log.Logger) error {
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		logger.Error(err.Error(), nil)
		return errors.New("unable to marshal stub resoruce")
	}

	err = json.Unmarshal(structJson, t)
	if err != nil {
		logger.Error(err.Error(), nil)
		return errors.New("unable to unmarshal stub resoruce")
	}

	return nil
}

func (t *StubResource) PublishState(logger *log.Logger) error {
	logger.Debugf("PublishState: %#v\n", *t)
	return nil
}

func (t *StubResource) RefreshState(logger *log.Logger) error {
	return nil
}

func (t *StubResource) SendLogs(logger *log.Logger) error {
	return nil
}

func (t *StubResource) SendMetrics(logger *log.Logger) error {
	return nil
}

func (t *StubResource) SendNotification(logger *log.Logger) error {
	logger.Debugf("Notification send: %#v\n", *t)
	return nil
}

func (t *StubResource) TakeAction(a Action, logger *log.Logger) error {
	logger.Debugf("taking action %#v on resource: %#v\n", a, *t)
	return nil
}

func (t *StubResource) GetType() Service {
	return SERVICE_STUB
}

func (t *StubResource) GetMetadata() map[string]interface{} {
	return map[string]interface{}{}
}
