package cloudinquisitor

import (
	"context"
	"encoding/json"
	"log"
)

func GetMockedLambdaContext() context.Context {
	ctx := context.Background()
	return ctx
}

func GetMockedPassableResourceAWSRoute53() PassableResource {
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
  },
  "StepFunctionExecutionID": "arn:aws:states:us-east-1:111111111111:execution:sample_sfn:12345678-abcd-abcd-abcd-0123456789ab"
}
`
	var passableResource PassableResource
	err := json.Unmarshal([]byte(passableResourceJSON), &passableResource)
	if err != nil {
		log.Fatalf("GetPassableResourceAWSRoute53 error %s", err)
	}

	return passableResource
}
