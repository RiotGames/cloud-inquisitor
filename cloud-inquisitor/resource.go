package cloudinquisitor

import (
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
	SERVICE_STUB    Service = "STUB"
	SERVICE_AWS_EC2 Service = "AWS_EC2"
	SERVICE_AWS_RDS Service = "AWS_RDS"
	SERVICE_AWS_S3  Service = "AWS_S3"
)

// Resource is an interaface that vaugely describes a
// cloud resource and what actions would be necessary to both
// collect information on the resource, audit and remediate it,
// and report the end result
type Resource interface {
	NewFromEventBus(events.CloudWatchEvent, *log.Logger) error
	NewFromPassableResource(PassableResource, *log.Logger) error
	// Audit determines if the current state of the struct
	// meets criteria for a given action
	Audit(*log.Logger) (Action, error)
	// PublishState is provided to give an easy hook to
	// send and store struct state in a backend data store
	PublishState(*log.Logger) error
	// RefreshState is provided to give an easy hook to
	// retrieve current resource information from the
	// cloud provider of choice
	RefreshState(*log.Logger) error
	// SendLogs is provided to give an easy hook for bulk
	// sending logs or other information to logging endpoints
	// if this is not taken care of inline
	SendLogs(*log.Logger) error
	// SendMetrics is provided to give an easy hook for
	// uploading application metrics to a metrics collector
	// if this is not taken care of already by the implementation
	SendMetrics(*log.Logger) error
	// SendNotification is provided to give an easy hook for
	// implementing various methods for sending status updates
	// via any medium
	SendNotification(*log.Logger) error
	// TakeAction is provided to give an easy hook for
	// taking custom actions against resources based on
	TakeAction(Action, *log.Logger) error
	// GetType returns an ENUM of the supported services
	GetType() Service
	// GetMetadata returns a map of Resoruce metadata
	GetMetadata() map[string]interface{}
}

// TaggableResource is an interface which introduces
// GetTags and GetMissingTags for a given resource
// Specifically for Auditing resource which can have a tag
type TaggableResource interface {
	Resource
	GetTags() map[string]string
	GetMissingTags() []string
}

type PassableResource struct {
	Resource interface{}
	Type     Service
	Finished bool
	Metadata map[string]interface{}
}

func (p PassableResource) GetResource(logger *log.Logger) (Resource, error) {
	switch p.Type {
	case SERVICE_STUB:
		stub := &StubResource{}
		err := stub.NewFromPassableResource(p, logger)
		return stub, err
	case SERVICE_AWS_RDS:
		rds := &AWSRDSInstance{}
		err := rds.NewFromPassableResource(p, logger)
		return rds, err
	case SERVICE_AWS_S3:
		s3 := &AWSS3Storage{}
		err := s3.NewFromPassableResource(p, logger)
		return s3, err
	default:
		return nil, errors.New("no matching resource for type " + p.Type)
	}
}

func NewResource(event events.CloudWatchEvent, logger *log.Logger) (Resource, error) {
	var resource Resource = nil
	switch event.Source {
	case "aws.ec2":
		logger.Debugf("parsing aws.ec2 taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
		resource = &StubResource{}
		err := resource.NewFromEventBus(event, logger)
		return resource, err

	case "aws.rds":
		logger.Debugf("parsing aws.rds taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
		resource = &AWSRDSInstance{}
		err := resource.NewFromEventBus(event, logger)
		return resource, err
	case "aws.s3":
		logger.Debugf("parsing aws.s3 taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
		resource = &AWSS3Storage{}
		err := resource.NewFromEventBus(event, logger)
		return resource, err
	default:
		logger.Warnf("error parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
		resource = &StubResource{}
		err := resource.NewFromEventBus(event, logger)
		return resource, err
	}
	return resource, nil
}

func NewTaggableResource(event events.CloudWatchEvent, logger *log.Logger) (TaggableResource, error) {
	var resource TaggableResource = nil
	switch event.Source {
	case "aws.ec2":
		logger.Debugf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	case "aws.rds":
		logger.Debugf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	case "aws.s3":
		logger.Debugf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	default:
		logger.Debugf("error parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	}
	return resource, nil
}
