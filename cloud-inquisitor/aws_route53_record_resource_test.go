package cloudinquisitor

import (
	"context"
	"encoding/json"
	"reflect"
	"testing"
)

func TestAWSRoute53RecordFromPassableResoruceCreateEvent(t *testing.T) {
	passableResourceJSON := `
{
  "Resource": {
    "AccountID": "123456789",
    "ZoneID": "zoneid",
    "EventName": "ChangeResourceRecordSets",
    "Action": "CREATE",
    "RecordType": "A",
    "RecordName": "localhost.",
    "RecordValues": [
      "127.0.0.1",
      "localhost"
    ],
    "Aliased": false,
    "Alias": {
      "ZoneId": "",
      "RecordName": ""
    }
  },
  "Type": "AWS_ROUTE53_RECORD",
  "Finished": true,
  "Metadata": {
    "unit-test": true
  }
}
`
	var passableResource PassableResource
	err := json.Unmarshal([]byte(passableResourceJSON), &passableResource)
	if err != nil {
		t.Fatal(err.Error())
	}
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
