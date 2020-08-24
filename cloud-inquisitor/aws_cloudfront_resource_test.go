package cloudinquisitor

import (
	"context"
	"encoding/json"
	"reflect"
	"testing"
)

func TestAWSCloudfrontRecordFromPassableResoruceCreateEvent(t *testing.T) {
	passableResourceJSON := `
	{
		"Resource": {
		  "AccountID": "123456789098",
		  "DistributionID": "X1X1X1X1X1X1X1",
		  "DomainName": "domain.cloudfront.net",
		  "EventName": "CreateDistribution",
		  "Origin": {
			"ID": "testid",
			"Domains": [
			  "testbucket.s3.amazonaws.com"
			]
		  }
		},
		"Type": "AWS_CLOUDFRONT",
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
	cf := &AWSCloudFrontDistributionHijackableResource{}
	cf.NewFromPassableResource(passableResource, context.Background(),
		map[string]interface{}{
			"marshalled": true,
		})

	if cf.GetLogger() == nil {
		t.Fatal("logger should not be nil")
	}

	metadata := cf.GetLogger().GetMetadata()
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

	cfMetadata := map[string]interface{}{
		"account":         cf.AccountID,
		"domain":          cf.DomainName,
		"distribution-id": cf.DistributionID,
		"event":           cf.EventName,
		"serviceType":     cf.GetType(),
	}

	if !reflect.DeepEqual(cfMetadata, cf.GetMetadata()) {
		t.Fatal("zone metadata is not what is expected")
	}
}
