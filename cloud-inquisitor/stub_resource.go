package cloudinquisitor

import (
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
	log.Printf("taking action %#v on resource: %#v\n", *t)
	return nil
}

func (t *StubResource) GetType() Service {
	return SERVICE_STUB
}
