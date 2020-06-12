package cloudinquisitor

import (
	"encoding/json"
	"errors"

	"github.com/aws/aws-lambda-go/events"
	log "github.com/sirupsen/logrus"
)

type StubResource struct {
	State int
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

func (t *StubResource) NewFromEventBus(event events.CloudWatchEvent) error {
	t.State = 0
	return nil
}

func (t *StubResource) NewFromPassableResource(resource PassableResource) error {
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		log.Error(err.Error())
		return errors.New("unable to marshal stub resoruce")
	}

	err = json.Unmarshal(structJson, t)
	if err != nil {
		log.Error(err.Error())
		return errors.New("unable to unmarshal stub resoruce")
	}

	return nil
}

func (t *StubResource) PublishState() error {
	log.Printf("PublishState: %#v\n", *t)
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
	log.Printf("Notification send: %#v\n", *t)
	return nil
}

func (t *StubResource) TakeAction(a Action) error {
	log.Printf("taking action %#v on resource: %#v\n", a, *t)
	return nil
}

func (t *StubResource) GetType() Service {
	return SERVICE_STUB
}

func (t *StubResource) GetMetadata() map[string]interface{} {
	return map[string]interface{}{}
}
