package cloudinquisitor

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	log "github.com/sirupsen/logrus"
)

type AWSRoute53Zone struct {
	State     int
	AccountID string
	ZoneName  string

	logger

	Tags     map[string]string
	Metadata map[string]interface{}
}

type AWSRoute53ZoneEventBusDetail struct {
	EventName         string `json:"eventName"`
	ErrorCode         string `json:"errorCode"`
	ErrorMessage      string `json:"errorMessage"`
	RequestParameters struct {
		Name             string `json:"name"`
		HostedZoneConfig struct {
			Comment     string `json:"comment"`
			PrivateZone bool   `json:"privateZone"`
		} `json:"hostedZoneConfig"`
	} `json:"requestParameters"`
	EventId string `json:"eventID"`
}

func (r *AWSRoute53Zone) NewFromEventBus(event events.CloudWatchEvent) error {
	err = json.Unmarshal(event.Detail)
}

func (s *AWSS3Storage) NewFromPassableResource(resource PassableResource) error {
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		log.Error(err.Error())
		return errors.New("unable to marshal stub resoruce")
	}

	err = json.Unmarshal(structJson, s)
	if err != nil {
		log.Error(err.Error())
		return errors.New("unable to unmarshal stub resoruce")
	}

	return nil
}

func (s *AWSS3Storage) Audit() (Action, error) {
	var result Action

	requiredTags, err := GetConfig("required_tags")
	if err != nil {
		return ACTION_ERROR, err
	}

	compliant := KeysInMap(s.Tags, strings.Split(requiredTags, ","))

	if compliant {
		return ACTION_FIXED_BY_USER, nil
	}

	switch s.State {
	case 0, 1, 2:
		result = ACTION_NOTIFY
	case 3:
		result = ACTION_PREVENT
	case 4:
		result = ACTION_REMOVE
	}

	s.State++

	return result, nil
}

func (s *AWSS3Storage) PublishState() error {
	log.Printf("PublishState: %#v\n", *s)
	return nil
}

func (s *AWSS3Storage) RefreshState() error {
	var AWSInputSession = session.Must(session.NewSession())
	assumedSession, err := AWSAssumeRole(s.AccountID, "ROLE_NAME", AWSInputSession)
	if err != nil {
		return err
	}

	s3Client := s3.New(assumedSession)

	taggingInput := &s3.GetBucketTaggingInput{
		Bucket: aws.String(s.BucketName),
	}

	tagsResult, err := s3Client.GetBucketTagging(taggingInput)
	if err != nil {
		return nil
	}

	s.Tags = map[string]string{}
	for _, tag := range tagsResult.TagSet {
		s.Tags[*tag.Key] = *tag.Value
	}
	return nil
}

func (s *AWSS3Storage) SendLogs() error {
	log.Printf("SendLogs: %#v\n", *s)
	return nil
}

func (s *AWSS3Storage) SendMetrics() error {
	log.Printf("SendMetrics: %#v\n", *s)
	return nil
}

func (s *AWSS3Storage) SendNotification() error {
	log.Printf("SendNotifcation: %#v\n", *s)
	return nil
}

func (s *AWSS3Storage) TakeAction(action Action) error {
	log.Printf("taking action %#v on resource: %#v\n", action, *s)

	actionMode, err := GetConfig("action_mode")
	if err != nil {
		return err
	}

	switch actionMode {
	case "dryrun":
		log.Printf("Dry-run mode specified")
		return nil
	case "normal":
		break
	default:
		return fmt.Errorf("Non-supported action mode: %v", actionMode)
	}

	assumedSession, err := AWSAssumeRole(s.AccountID, "ROLE_NAME", nil)
	if err != nil {
		return err
	}

	s3Client := s3.New(assumedSession)

	switch action {
	case ACTION_PREVENT:
		// apply prevent policy
		inputPutPolicy := &s3.PutBucketPolicyInput{
			Bucket:                        aws.String(s.BucketName),
			ConfirmRemoveSelfBucketAccess: aws.Bool(true),
			Policy:                        aws.String(strings.ReplaceAll(s3PreventPolicy, "BUCKETNAME", s.BucketName)),
		}

		outputPutPolicy, err := s3Client.PutBucketPolicy(inputPutPolicy)
		if err != nil {
			return err
		}

		log.Printf("Output of PREVENT for bucket %s: %s\n", s.BucketName, outputPutPolicy.String())
	case ACTION_REMOVE:
		// delete bucket
		inputListObjects := &s3.ListObjectsV2Input{
			Bucket: aws.String(s.BucketName),
		}

		var listErr error = nil
		s3Client.ListObjectsV2Pages(inputListObjects, func(page *s3.ListObjectsV2Output, last bool) bool {
			for _, object := range page.Contents {
				log.Printf("Deleting from Bucket %s Object %s\n", s.BucketName, *object.Key)
				inputDeleteObject := &s3.DeleteObjectInput{
					Bucket: aws.String(s.BucketName),
					Key:    object.Key,
				}

				outputDeleteObject, err := s3Client.DeleteObject(inputDeleteObject)
				if err != nil {
					listErr = err
					// close out regardless
					return false
				}

				log.Printf("Deleted from Bucket %s Object %s with output %s\n", s.BucketName, *object.Key, outputDeleteObject.String())
			}

			return !last
		})

		if listErr != nil {
			return listErr
		}

		log.Printf("Deleting Bucket %s\n", s.BucketName)
		inputDeleteBucket := &s3.DeleteBucketInput{
			Bucket: aws.String(s.BucketName),
		}

		outputDeleteBucket, err := s3Client.DeleteBucket(inputDeleteBucket)
		if err != nil {
			return err
		}

		log.Printf("Deleted Bucket %s with output %s\n", s.BucketName, outputDeleteBucket.String())

	default:
		return nil
	}

	return nil
}

func (s3 *AWSS3Storage) GetType() Service {
	return SERVICE_AWS_S3
}
