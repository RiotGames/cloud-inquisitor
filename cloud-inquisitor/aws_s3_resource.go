package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	openapis3 "github.com/RiotGames/cloud-inquisitor/ext/aws/s3"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/sirupsen/logrus"
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
	logger     *log.Logger

	Tags map[string]string
}

func (s *AWSS3Storage) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passsedInMetadata map[string]interface{}) error {
	defaultMetadata, err := DefaultLambdaMetadata(ctx)
	if err != nil {
		return err
	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passsedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range defaultMetadata {
		mergedMetaData[k] = v
	}

	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}
	s.logger = instrument.GetInstrumentedLogger(opts, ctx)

	s.logger.WithFields(mergedMetaData).Debug("marshalling new event")
	eventBytes, err := json.Marshal(event)
	if err != nil {
		s.logger.Error("error marshalling: "+err.Error(), nil)
		return err
	}

	s.logger.Debug("unmarshalling event to openapi s3 event", nil)
	var s3OpenAPI openapis3.AwsEvent
	err = json.Unmarshal(eventBytes, &s3OpenAPI)
	if err != nil {
		s.logger.Error("error unmarshalling: "+err.Error(), nil)
		return err
	}

	s.State = 0
	s.AccountID = s3OpenAPI.Account
	s.Region = s3OpenAPI.Region
	s.BucketName = s3OpenAPI.Detail.RequestParameters.BucketName

	err = s.RefreshState()
	if err == nil {
		s.logger.WithFields(s.GetMetadata()).Info("new resource created")
	}
	return err
}

func (s *AWSS3Storage) NewFromPassableResource(resource PassableResource, ctx context.Context, passsedInMetadata map[string]interface{}) error {
	lamdbaMetadata, err := LambdaMetadataFromPassableResource(ctx, resource)
	if err != nil {
		return err

	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passsedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range lamdbaMetadata {
		mergedMetaData[k] = v
	}
	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}
	s.logger = instrument.GetInstrumentedLogger(opts, ctx)
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		s.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-s3",
			"cloud-inquisitor-error":    "json marshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-s3 resource")
	}

	err = json.Unmarshal(structJson, s)
	if err != nil {
		s.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-s3",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-s3 resource")
	}

	return nil
}

func (s *AWSS3Storage) Audit() (Action, error) {
	var result Action

	requiredTags := settings.GetString("auditing.required_tags")

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
	s.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-s3",
	}).Debugf("PublishState: %#v", *s)
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
	s.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-s3",
	}).Debugf("SendLogs: %#v", *s)
	return nil
}

func (s *AWSS3Storage) SendMetrics() error {
	s.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-s3",
	}).Debugf("SendMetrics: %#v", *s)
	return nil
}

func (s *AWSS3Storage) SendNotification() error {
	s.logger.WithFields(logrus.Fields{"cloud-inquisitor-resource": "aws-s3"}).Debugf("SendNotifcation: %#v", *s)
	return nil
}

func (s *AWSS3Storage) TakeAction(action Action) error {
	actionMode := settings.GetString("actions.mode")
	s.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource":    "aws-s3",
		"cloud-inquisitor-action":      action,
		"cloud-inquisitor-action-mode": actionMode,
	}).WithFields(s.GetMetadata()).Infof("taking action %#v on resource: %#v", action, *s)

	switch actionMode {
	case "dryrun":
		return nil
	case "normal":
		break
	default:
		s.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource":    "aws-s3",
			"cloud-inquisitor-action":      action,
			"cloud-inquisitor-action-mode": actionMode,
			"cloud-inquisitor-error":       "unsupported action"}).WithFields(s.GetMetadata()).Error("unsuported action")
		return fmt.Errorf("non-supported action mode: %v", actionMode)
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

		s.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource":    "aws-s3",
			"cloud-inquisitor-action":      action,
			"cloud-inquisitor-action-mode": actionMode}).WithFields(s.GetMetadata()).Debugf("output of PREVENT for bucket %s: %s", s.BucketName, outputPutPolicy.String())
	case ACTION_REMOVE:
		// delete bucket
		inputListObjects := &s3.ListObjectsV2Input{
			Bucket: aws.String(s.BucketName),
		}

		var listErr error = nil
		s3Client.ListObjectsV2Pages(inputListObjects, func(page *s3.ListObjectsV2Output, last bool) bool {
			for _, object := range page.Contents {
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

				s.logger.WithFields(logrus.Fields{
					"cloud-inquisitor-resource":    "aws-s3",
					"cloud-inquisitor-action":      action,
					"cloud-inquisitor-action-mode": actionMode}).WithFields(s.GetMetadata()).Infof("deleted from Bucket %s Object %s with output %s", s.BucketName, *object.Key, outputDeleteObject.String())
			}

			return !last
		})

		if listErr != nil {
			return listErr
		}

		s.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource":    "aws-s3",
			"cloud-inquisitor-action":      action,
			"cloud-inquisitor-action-mode": actionMode}).WithFields(s.GetMetadata()).Infof("deleting Bucket %s", s.BucketName)
		inputDeleteBucket := &s3.DeleteBucketInput{
			Bucket: aws.String(s.BucketName),
		}

		outputDeleteBucket, err := s3Client.DeleteBucket(inputDeleteBucket)
		if err != nil {
			return err
		}

		s.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource":    "aws-s3",
			"cloud-inquisitor-action":      action,
			"cloud-inquisitor-action-mode": actionMode,
		}).WithFields(s.GetMetadata()).Infof("deleted Bucket %s with output %s", s.BucketName, outputDeleteBucket.String())

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

func (s3 *AWSS3Storage) GetLogger() *log.Logger {
	return s3.logger
}

func (s3 *AWSS3Storage) GetTags() map[string]string {
	return s3.Tags
}

func (s3 *AWSS3Storage) GetMissingTags() []string {
	requiredTags := settings.GetString("auditing.required_tags")
	missingTags := []string{}
	for _, tag := range strings.Split(requiredTags, ",") {
		if _, ok := s3.Tags[tag]; !ok {
			missingTags = append(missingTags, tag)
		}
	}

	return missingTags
}
