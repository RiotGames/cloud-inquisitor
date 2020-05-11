package cloudinquisitor

import (
	"github.com/aws/aws-lambda-go/events"

	log "github.com/sirupsen/logrus"
)

type Action = byte

const (
	ACTION_ERROR Action = iota
	ACTION_NOTIFY
	ACTION_PREVENT
	ACTION_REMOVE
)

// Resource is an interaface that vaugely describes a
// cloud resource and what actions would be necessary to both
// collect information on the resource, audit and remediate it,
// and report the end result
type Resource interface {
	// Audit determines if the current state of the struct
	// meets criteria for a given action
	Audit() (Action, error)
	// PublishState is provided to give an easy hook to
	// send and store struct state in a backend data store
	PublishState() error
	// RefreshState is provided to give an easy hook to
	// retrieve current resource information from the
	// cloud provider of choice
	RefreshState() error
	// SendLogs is provided to give an easy hook for bulk
	// sending logs or other information to logging endpoints
	// if this is not taken care of inline
	SendLogs() error
	// SendMetrics is provided to give an easy hook for
	// uploading application metrics to a metrics collector
	// if this is not taken care of already by the implementation
	SendMetrics() error
	// SendNotification is provided to give an easy hook for
	// implementing various methods for sending status updates
	// via any medium
	SendNotification() error
	// TakeAction is provided to give an easy hook for
	// taking custom actions against resources based on
	TakeAction(Action) error
}

// TaggableResource is an interface which introduces
// GetTags and GetMissingTags for a given resource
// Specifically for Auditing resource which can have a tag
type TaggableResource interface {
	Resource
	GetTags() map[string]string
	GetMissingTags() []string
}

func NewResource(event events.CloudWatchEvent) (ResourceResource, error) {
	var resource Resource = nil
	switch event.Source {
	case "aws.ec2":
		log.Printf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	case "aws.rds":
		log.Printf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	case "aws.s3":
		log.Printf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	default:
		log.Warningf("error parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	}
	return resource, nil
}

func NewTaggableResource(event events.CloudWatchEvent) (TaggableResource, error) {
	var resource TaggableResource = nil
	switch event.Source {
	case "aws.ec2":
		log.Printf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	case "aws.rds":
		log.Printf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	case "aws.s3":
		log.Printf("parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	default:
		log.Warningf("error parsing taggable resources: {%v, %v, %v, %v}\n", event.Resources, event.Region, event.Source, event.AccountID)
	}
	return resource, nil
}
