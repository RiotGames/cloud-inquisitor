package cloudinquisitor

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	openapis3 "github.com/RiotGames/cloud-inquisitor/ext/aws/s3"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	log "github.com/sirupsen/logrus"
)

const (
	s3PreventPolicy = `{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudInquisitor",
            "Effect": "Deny",
            "Principal": "*",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::BUCKETNAME/*"
            ]
        }
    ]
}`
)

type AWSS3Storage struct {
	State      int
	AccountID  string
	Region     string
	BucketName string

	Tags map[string]string
}

func (s *AWSS3Storage) NewFromEventBus(event events.CloudWatchEvent) error {
	eventBytes, err := json.Marshal(event)
	if err != nil {
		return err
	}

	var s3OpenAPI openapis3.AwsEvent
	err = json.Unmarshal(eventBytes, &s3OpenAPI)
	if err != nil {
		return err
	}

	s.State = 0
	s.AccountID = s3OpenAPI.Account
	s.Region = s3OpenAPI.Region
	s.BucketName = s3OpenAPI.Detail.RequestParameters.BucketName

	err = s.RefreshState()
	return err
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

	requiredTags := settings.GetString("auditing.required_tags")

	compliant := true
	for _, tag := range strings.Split(requiredTags, ",") {
		if _, ok := s.Tags[tag]; !ok {
			compliant = false
			break
		}
	}

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

	actionMode := settings.GetString("actions.mode")

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

func (s3 *AWSS3Storage) GetMetadata() map[string]interface{} {
	return map[string]interface{}{
		"account":      s3.AccountID,
		"region":       s3.Region,
		"bucketName":   s3.BucketName,
		"currentState": s3.State,
		"tags":         s3.Tags,
	}
}
