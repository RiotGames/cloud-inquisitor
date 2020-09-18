package cloudinquisitor

import (
	"encoding/json"
	"log"

	"github.com/aws/aws-lambda-go/lambdacontext"
)

func GetMockedLambdaContext() lambdacontext.LambdaContext {
	return lambdacontext.LambdaContext{
		AwsRequestID:       "SAMPLE_REQUEST_ID",
		InvokedFunctionArn: "SAMPLE_ARN",
	}
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
	"unit-test": true,
	
	"AccountID": "123456789",
	"Region": "us-west-2",
	"ActionName": "SAMPLE_ACTION",
	"ResourceARN": "",
	"ResourceID": "",
	"ResourceName": "",
	"ResourceType": "",
	"ResourceSubType": ""
  },
  "StepFunctionExecutionID": "SAMPLE_SFN_EXE_ID"
}
`
	var passableResource PassableResource
	err := json.Unmarshal([]byte(passableResourceJSON), &passableResource)
	if err != nil {
		log.Fatalf("GetPassableResourceAWSRoute53 error %s", err)
	}

	return passableResource
}
