package cloudinquisitor

import (
	"context"
	"encoding/json"
	"reflect"
	"testing"
)

func TestAWSRoute53ZoneFromPassableResoruceCreateEvent(t *testing.T) {
	passableResourceJSON := `
{
  "Resource": {
    "AccountID": "123456789",
    "ZoneName": "unittest.cloudinquisitor",
    "ZoneID": "testzone",
    "EventName": "CreateHostedZone",
    "ChangeId": "/change/changeid",
    "Type": "AWS_ROUTE53_ZONE"
  },
  "Type": "AWS_ROUTE53_ZONE",
  "Finished": false,
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
	zone := &AWSRoute53Zone{}
	zone.NewFromPassableResource(passableResource, context.Background(),
		map[string]interface{}{
			"marshalled": true,
		})

	if zone.GetLogger() == nil {
		t.Fatal("logger should not be nil")
	}

	metadata := zone.GetLogger().GetMetadata()
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

	zoneMetadata := map[string]interface{}{
		"account":     zone.AccountID,
		"zone":        zone.ZoneName,
		"zone-id":     zone.ZoneID,
		"event":       zone.EventName,
		"serviceType": zone.Type,
	}

	if !reflect.DeepEqual(zoneMetadata, zone.GetMetadata()) {
		t.Fatal("zone metadata is not what is expected")
	}
}
