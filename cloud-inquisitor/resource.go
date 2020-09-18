package cloudinquisitor

import (
	"context"
	"errors"

	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/aws/aws-lambda-go/events"
	//"github.com/sirupsen/logrus"
)

type Action = string
type Service = string

const (
	ACTION_ERROR         Action = "ACTION_ERROR"
	ACTION_NOTIFY        Action = "ACTION_NOTIFY"
	ACTION_PREVENT       Action = "ACTION_PREVENT"
	ACTION_REMOVE        Action = "ACTION_REMOVE"
	ACTION_FIXED_BY_USER Action = "ACTION_FIXED_BY_USER"
	ACTION_NONE          Action = "ACTION_NONE"
)

const (
	SERVICE_STUB                   Service = "STUB"
	SERVICE_AWS_EC2                Service = "AWS_EC2"
	SERVICE_AWS_RDS                Service = "AWS_RDS"
	SERVICE_AWS_S3                 Service = "AWS_S3"
	SERVICE_AWS_ROUTE53_ZONE       Service = "AWS_ROUTE53_ZONE"
	SERVICE_AWS_ROUTE53_RECORD     Service = "AWS_ROUTE53_RECORD"
	SERVICE_AWS_ROUTE53_RECORD_SET Service = "AWS_ROUTE53_RECORD_SET"
	SERVICE_AWS_CLOUDFRONT         Service = "AWS_CLOUDFRONT"
	SERVICE_AWS_ELASTICBEANSTALK   Service = "AWS_ELASTICBEANSTALK"
)

// Resource is an interaface that vaugely describes a
// cloud resource and what actions would be necessary to both
// collect information on the resource, audit and remediate it,
// and report the end result
type Resource interface {
	// RefreshState is provided to give an easy hook to
	// retrieve current resource information from the
	// cloud provider of choice
	RefreshState() error
	// SendNotification is provided to give an easy hook for
	// implementing various methods for sending status updates
	// via any medium
	SendNotification() error
	// GetType returns an ENUM of the supported services
	GetType() Service
	// GetMetadata returns a map of Resoruce metadata
	GetMetadata() map[string]interface{}
	GetLogger() *log.Logger
}

// TaggableResource is an interface which introduces
// GetTags and GetMissingTags for a given resource
// Specifically for Auditing resource which can have a tag
type TaggableResource interface {
	Resource
	NewFromEventBus(events.CloudWatchEvent, context.Context, map[string]interface{}) error
	NewFromPassableResource(PassableResource, context.Context, map[string]interface{}) error
	// TakeAction is provided to give an easy hook for
	// taking custom actions against resources based on
	TakeAction(Action) error
	// Audit determines if the current state of the struct
	// meets criteria for a given action
	Audit() (Action, error)
	GetTags() map[string]string
	GetMissingTags() []string
}

type PassableResource struct {
	Resource                interface{}
	Type                    Service
	Finished                bool
	Metadata                map[string]interface{}
	StepFunctionExecutionID string
}

func (p PassableResource) GetTaggableResource(ctx context.Context, metadata map[string]interface{}) (TaggableResource, error) {
	switch p.Type {
	case SERVICE_STUB:
		stub := &StubResource{}
		err := stub.NewFromPassableResource(p, ctx, metadata)
		return stub, err
	case SERVICE_AWS_RDS:
		rds := &AWSRDSInstance{}
		err := rds.NewFromPassableResource(p, ctx, metadata)
		return rds, err
	case SERVICE_AWS_S3:
		s3 := &AWSS3Storage{}
		err := s3.NewFromPassableResource(p, ctx, metadata)
		return s3, err
	default:
		return nil, errors.New("no matching resource for type " + p.Type)
	}
}

func NewTaggableResource(event events.CloudWatchEvent, ctx context.Context, metadata map[string]interface{}) (TaggableResource, error) {
	var resource TaggableResource = nil
	switch event.Source {
	case "aws.ec2":
		resource = &StubResource{}
		err := resource.NewFromEventBus(event, ctx, metadata)
		return resource, err

	case "aws.rds":
		resource = &AWSRDSInstance{}
		err := resource.NewFromEventBus(event, ctx, metadata)
		return resource, err

	case "aws.s3":
		resource = &AWSS3Storage{}
		err := resource.NewFromEventBus(event, ctx, metadata)
		return resource, err

	default:
		resource = &StubResource{}
		err := resource.NewFromEventBus(event, ctx, metadata)
		return resource, err

	}
	return resource, nil
}
