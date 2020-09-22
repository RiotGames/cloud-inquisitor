package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	"github.com/aws/aws-lambda-go/events"
	//"github.com/sirupsen/logrus"
)

type HijackableResource interface {
	Resource
	NewFromEventBus(events.CloudWatchEvent, context.Context, map[string]interface{}) error
	NewFromPassableResource(PassableResource, context.Context, map[string]interface{}) error
	AnalyzeForHijack() (*model.HijackableResourceChain, error)
	// PublishState is provided to give an easy hook to
	// send and store struct state in a backend data store
	PublishState() error
}

func (p PassableResource) GetHijackableResource(ctx context.Context, metadata map[string]interface{}) (HijackableResource, error) {
	switch p.Type {
	case SERVICE_STUB:
		stub := &StubResource{}
		err := stub.NewFromPassableResource(p, ctx, metadata)
		return stub, err
	case SERVICE_AWS_ROUTE53_ZONE:
		r53 := &AWSRoute53Zone{}
		err := r53.NewFromPassableResource(p, ctx, metadata)
		return r53, err
	case SERVICE_AWS_ROUTE53_RECORD:
		r53 := &AWSRoute53Record{}
		err := r53.NewFromPassableResource(p, ctx, metadata)
		return r53, err
	case SERVICE_AWS_CLOUDFRONT:
		cf := &AWSCloudFrontDistributionHijackableResource{}
		err := cf.NewFromPassableResource(p, ctx, metadata)
		return cf, err
	case SERVICE_AWS_ELASTICBEANSTALK:
		eb := &AWSElasticBeanstalkEnvironmentHijackableResource{}
		err := eb.NewFromPassableResource(p, ctx, metadata)
		return eb, err
	case SERVICE_AWS_S3:
		s3 := &AWSS3StorageHijackableResource{}
		err := s3.NewFromPassableResource(p, ctx, metadata)
		return s3, err
	default:
		return nil, errors.New("no matching resource for type " + p.Type)
	}
}

func NewHijackableResource(event events.CloudWatchEvent, ctx context.Context, metadata map[string]interface{}) (HijackableResource, error) {
	var resource HijackableResource = nil
	switch event.Source {
	case "aws.route53":
		detailMap := map[string]interface{}{}
		err := json.Unmarshal(event.Detail, &detailMap)
		if err != nil {
			return resource, err
		}
		if eventName, ok := detailMap["eventName"]; ok {
			switch eventName {
			case "CreateHostedZone":
				resource = &AWSRoute53Zone{}
				resourceErr := resource.NewFromEventBus(event, ctx, metadata)
				return resource, resourceErr
			case "ChangeResourceRecordSets":
				resource = &AWSRoute53RecordSet{}
				resourceErr := resource.NewFromEventBus(event, ctx, metadata)
				return resource, resourceErr
			default:
				resource = &StubResource{}
				return resource, errors.New("unknown route53 eventName")
			}
		} else {
			resource = &StubResource{}
			return resource, errors.New("unable to parse evetName from map")
		}
	case "aws.cloudfront":
		resource = &AWSCloudFrontDistributionHijackableResource{}
		resourceErr := resource.NewFromEventBus(event, ctx, metadata)
		return resource, resourceErr
	case "aws.elasticbeanstalk":
		detailMap := map[string]interface{}{}
		err := json.Unmarshal(event.Detail, &detailMap)
		if err != nil {
			return resource, err
		}
		if eventName, ok := detailMap["eventName"]; ok {
			switch eventName {
			case "TerminateEnvironment", "CreateEnvironment":
				resource = &AWSElasticBeanstalkEnvironmentHijackableResource{}
				resourceErr := resource.NewFromEventBus(event, ctx, metadata)
				return resource, resourceErr
			default:
				resource = &StubResource{}
				return resource, errors.New("unknown elasticbeanstalk eventName")
			}
		} else {
			resource = &StubResource{}
			return resource, errors.New("unable to parse evetName from map")
		}
	case "aws.s3":
		detailMap := map[string]interface{}{}
		err := json.Unmarshal(event.Detail, &detailMap)
		if err != nil {
			return resource, err
		}
		if eventName, ok := detailMap["eventName"]; ok {
			switch eventName {
			case "CreateBucket", "DeleteBucket":
				resource = &AWSS3StorageHijackableResource{}
				resourceErr := resource.NewFromEventBus(event, ctx, metadata)
				return resource, resourceErr
			default:
				resource = &StubResource{}
				return resource, errors.New("unknown s3 eventName")
			}
		} else {
			resource = &StubResource{}
			return resource, errors.New("unable to parse evetName from map")
		}
	default:
		resource = &StubResource{}
		err := resource.NewFromEventBus(event, ctx, metadata)
		return resource, err

	}
	return resource, nil
}
