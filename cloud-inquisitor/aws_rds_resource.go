package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/rds"
	"github.com/sirupsen/logrus"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	openapi_aws_rds "github.com/RiotGames/cloud-inquisitor/ext/aws/rds"
)

// AWSRDSInstance - AWS RDS Instance
type AWSRDSInstance struct {
	State        int
	AccountID    string
	Region       string
	ResourceArn  string
	ResourceID   string
	ResourceType string

	DiskSpace          int64
	Engine             string
	InstanceClass      string
	InstanceStatus     string
	PubliclyAccessible bool

	Tags map[string]string

	logger *log.Logger
}

// Audit : AWS RDS Instance Audit
func (r *AWSRDSInstance) Audit() (Action, error) {
	var result Action

	requiredTags := settings.GetString("auditing.required_tags")

	compliant := KeysInMap(r.Tags, strings.Split(requiredTags, ","))

	if compliant {
		return ACTION_FIXED_BY_USER, nil
	}

	switch r.State {
	case 0, 1, 2:
		result = ACTION_NOTIFY
	case 3:
		result = ACTION_PREVENT
	case 4:
		result = ACTION_REMOVE
	}

	r.State++

	return result, nil
}

// NewFromEventBus -
func (r *AWSRDSInstance) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passedInMetadata map[string]interface{}) error {
	defaultMetadata, err := DefaultLambdaMetadata(ctx)
	if err != nil {
		return err
	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range defaultMetadata {
		mergedMetaData[k] = v
	}

	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}

	r.logger = instrument.GetInstrumentedLogger(opts, ctx)
	eventBytes, err := json.Marshal(event)
	if err != nil {
		return err
	}

	var RDSOpenAPI openapi_aws_rds.AwsEvent
	err = json.Unmarshal(eventBytes, &RDSOpenAPI)
	if err != nil {
		return err
	}

	idBuf := strings.Split(RDSOpenAPI.Detail.SourceArn, ":")

	r.AccountID = RDSOpenAPI.Account
	r.Region = RDSOpenAPI.Region
	r.ResourceArn = RDSOpenAPI.Detail.SourceArn
	r.ResourceID = idBuf[len(idBuf)-1]
	r.State = 0
	return nil
}

// NewFromPassableResource -
func (r *AWSRDSInstance) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
	defaultMetadata, err := DefaultLambdaMetadata(ctx)
	if err != nil {
		return err
	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range defaultMetadata {
		mergedMetaData[k] = v
	}

	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}
	r.logger = instrument.GetInstrumentedLogger(opts, ctx)

	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-rds",
			"cloud-inquisitor-error":    "json marshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-rds resource")
	}

	err = json.Unmarshal(structJson, r)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-rds",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-srds resource")
	}
	return nil
}

// PublishState -
func (r *AWSRDSInstance) PublishState() error {
	r.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-rds",
	}).WithFields(r.GetMetadata()).Debugf("PublishState: %#v", *r)
	return nil
}

// RefreshState -
func (r *AWSRDSInstance) RefreshState() error {
	var AWSInputSession = session.Must(session.NewSession())
	assumedSession, err := AWSAssumeRole(r.AccountID, "ROLE_NAME", AWSInputSession)

	rdsClient := rds.New(
		assumedSession,
		&aws.Config{Region: aws.String(r.Region)},
	)
	output, err := rdsClient.DescribeDBInstances(
		&rds.DescribeDBInstancesInput{DBInstanceIdentifier: aws.String(r.ResourceID)},
	)

	if err != nil || len(output.DBInstances) < 1 {
		return err
	}

	r.DiskSpace = *output.DBInstances[0].AllocatedStorage
	r.InstanceClass = *output.DBInstances[0].DBInstanceClass
	r.InstanceStatus = *output.DBInstances[0].DBInstanceStatus
	r.PubliclyAccessible = *output.DBInstances[0].PubliclyAccessible

	input := &rds.ListTagsForResourceInput{ResourceName: &r.ResourceArn}
	result, err := rdsClient.ListTagsForResource(input)

	if err != nil {
		return err
	}

	r.Tags = make(map[string]string)
	for _, tag := range result.TagList {
		r.Tags[*tag.Key] = *tag.Value
	}

	return nil
}

// SendLogs -
func (t *AWSRDSInstance) SendLogs() error {
	return nil
}

// SendMetrics -
func (r *AWSRDSInstance) SendMetrics() error {
	return nil
}

// SendNotification -
func (r *AWSRDSInstance) SendNotification() error {
	r.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-rds",
	}).WithFields(r.GetMetadata()).Debugf("Notification send: %#v", *r)
	return nil
}

// TakeAction -
func (r *AWSRDSInstance) TakeAction(a Action) error {
	r.logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-rds",
	}).WithFields(r.GetMetadata()).Infof("taking action %#v on resource: %#v\n", a, *r)

	actionMode := settings.GetString("actions.mode")

	switch actionMode {
	case "dryrun":
		return nil
	case "normal":
		break
	default:
		return fmt.Errorf("Non-supported action mode: %v", actionMode)
	}

	assumedSession, err := AWSAssumeRole(r.AccountID, "ROLE_NAME", nil)
	if err != nil {
		return err
	}

	rdsClient := rds.New(
		assumedSession,
		&aws.Config{Region: aws.String(r.Region)},
	)

	switch a {
	case ACTION_PREVENT:
		// Stop RDS instance
		switch r.InstanceStatus {
		case "available":
			_, err := rdsClient.StopDBInstance(&rds.StopDBInstanceInput{
				DBInstanceIdentifier: aws.String(r.ResourceID)})

			if err != nil {
				return err
			}
		case "stopped":
			return nil

		}

	case ACTION_REMOVE:
		// Remove Deletion Protection
		_, err := rdsClient.ModifyDBInstance(&rds.ModifyDBInstanceInput{
			DBInstanceIdentifier: aws.String(r.ResourceID),
			DeletionProtection:   aws.Bool(false)})

		if err != nil {
			return err
		}

		timeFormat := settings.GetString("timestamp_format")

		dbSnapshotIdentifier := fmt.Sprintf(
			"cinq-snapshot-%s-%s",
			r.ResourceID,
			time.Now().UTC().Format(timeFormat),
		)

		// Create a final snapshot and delete RDS instance
		switch r.InstanceStatus {
		case "available", "stopped":
			_, err := rdsClient.DeleteDBInstance(
				&rds.DeleteDBInstanceInput{
					DBInstanceIdentifier:      aws.String(r.ResourceID),
					DeleteAutomatedBackups:    aws.Bool(false),
					FinalDBSnapshotIdentifier: aws.String(dbSnapshotIdentifier)},
			)

			if err != nil {
				return err
			}

		}
	}

	return nil
}

// GetType -
func (r *AWSRDSInstance) GetType() Service {
	return SERVICE_AWS_RDS
}

func (rds *AWSRDSInstance) GetMetadata() map[string]interface{} {
	return map[string]interface{}{
		"region":       rds.Region,
		"account":      rds.AccountID,
		"resourceName": rds.ResourceID,
		"currentState": rds.State,
	}
}

func (r *AWSRDSInstance) GetLogger() *log.Logger {
	return r.logger
}
