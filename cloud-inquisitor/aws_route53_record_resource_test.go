package cloudinquisitor

import (
	"context"
	"reflect"
	"testing"
)

func TestAWSRoute53RecordFromPassableResoruceCreateEvent(t *testing.T) {
	passableResource := GetMockedPassableResourceAWSRoute53()
	record := &AWSRoute53Record{}
	record.NewFromPassableResource(passableResource, context.Background(),
		map[string]interface{}{
			"marshalled": true,
		})

	if record.GetLogger() == nil {
		t.Fatal("logger should not be nil")
	}

	metadata := record.GetLogger().GetMetadata()
	t.Logf("got logger metadata: %#v\n", metadata)
	if val, ok := metadata["unit-test"]; !ok {
		t.Fatal("metadata key \"unit-test\" missing")
	} else {
		if val.(bool) != true {
			t.Fatal("metadata value for key \"unit-test\" is not true")
		}
	}
	if val, ok := metadata["marshalled"]; !ok {
		t.Fatal("metadata key \"marshalled\" missing")
	} else {
		if val.(bool) != true {
			t.Fatal("metadata value for key \"marshalled\" is not true")
		}
	}

	recordMetadata := map[string]interface{}{
		"account":      record.AccountID,
		"zoneId":       record.ZoneID,
		"eventName":    record.EventName,
		"action":       record.Action,
		"recordType":   record.RecordType,
		"recordName":   record.RecordName,
		"recordValues": record.RecordValues,
	}

	if !reflect.DeepEqual(recordMetadata, record.GetMetadata()) {
		t.Fatal("zone metadata is not what is expected")
	}
}
