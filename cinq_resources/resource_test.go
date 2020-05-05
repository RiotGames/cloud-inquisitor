package resource

import (
	"errors"
	"testing"
)

type testResource struct {
	state int
	tags map[string]string
}

func (t *testResource) Audit() (Action, error) {
	switch t.state {
	case 0, 1, 2:
		t.state += 1
		return ACTION_NOTIFY, nil
	case 3:
		t.state += 1
		return ACTION_PREVENT, nil
	case 4:
		t.state += 1
		return ACTION_REMOVE, nil
	default:
		t.state = 0
		return ACTION_ERROR, errors.New("hit default case")
	}
}
func (t *testResource) PublishState() error {
	return nil
}
func (t *testResource) RefreshState() error {
	return nil
}
func (t *testResource) SendLogs() error {
	return nil
}
func (t *testResource) SendMetrics() error {
	return nil
}
func (t *testResource) SendNotification() error {
	return nil
}
func (t *testResource) TakeAction(Action) error {
	return nil
}

func (t *testResource) GetTags() map[string]string {
	return t.tags
}

func (t *testResource) GetMissingTags() []string {
	knownTags := []string{"tag1", "tag2", "tag3"}
	missingTags := []string{}

	for _, knownTag := range knownTags {
		if _, ok := t.tags[knownTag]; !ok {
			missingTags = append(missingTags, knownTag)
		}
	}

	return missingTags
}


func TestResourceInterface(t *testing.T) {
	tresource := &testResource{}
	var iresource Resource

	iresource = tresource
	if _, ok := iresource.(*testResource); !ok {
		t.Fatal("testResource should implement Resource interface")
	}
}

func TestTaggableResourceInterface(t *testing.T) {
	tresource := &testResource{}

	var iresource TaggableResource
	iresource = tresource
	if _, ok := iresource.(*testResource); !ok {
		t.Fatal("testResource should implement TaggableResource interface")
	}
}

func TestAuditTaggableResource(t *testing.T) {
	tResoruce := &testResource{}

	for i := 0; i < 6; i += 1 {
		switch i {
		case 0, 1, 2:
			action, err := tResoruce.Audit()
			if err != nil {
				t.Fatal(err.Error())
			}

			if action != ACTION_NOTIFY {
				t.Fatal("action should be ACTION_NOTIFY not ", action)
			}
		case 3:
			action, err := tResoruce.Audit()
			if err != nil {
				t.Fatal(err.Error())
			}

			if action != ACTION_PREVENT {
				t.Fatal("action should be ACTION_PREVENT not ", action)
			}
		case 4:
			action, err := tResoruce.Audit()
			if err != nil {
				t.Fatal(err.Error())
			}

			if action != ACTION_REMOVE {
				t.Fatal("action should be ACTION_REMOVE not ", action)
			}
		case 5:
			action, err := tResoruce.Audit()
			if err == nil {
				t.Fatal("error should have been returned")
			}

			if action != ACTION_ERROR {
				t.Fatal("action should be ACTION_ERROR not ", action)
			}
		}
	}
}