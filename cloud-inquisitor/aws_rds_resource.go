package cloudinquisitor

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

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
}

// Audit : AWS RDS Instance Audit
func (t *AWSRDSInstance) Audit(logger *log.Logger) (Action, error) {
	var result Action

	requiredTags := settings.GetString("auditing.required_tags")

	compliant := true
	for _, tag := range strings.Split(requiredTags, ",") {
		if _, ok := t.Tags[tag]; !ok {
			compliant = false
			break
		}
	}

	if compliant {
		return ACTION_FIXED_BY_USER, nil
	}

	switch t.State {
	case 0, 1, 2:
		result = ACTION_NOTIFY
	case 3:
		result = ACTION_PREVENT
	case 4:
		result = ACTION_REMOVE
	}

	t.State++

	return result, nil
}

// NewFromEventBus -
func (t *AWSRDSInstance) NewFromEventBus(event events.CloudWatchEvent, logger *log.Logger) error {
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

	t.AccountID = RDSOpenAPI.Account
	t.Region = RDSOpenAPI.Region
	t.ResourceArn = RDSOpenAPI.Detail.SourceArn
	t.ResourceID = idBuf[len(idBuf)-1]
	t.State = 0

	return nil
}

// NewFromPassableResource -
func (t *AWSRDSInstance) NewFromPassableResource(resource PassableResource, logger *log.Logger) error {
	return nil
}

// PublishState -
func (t *AWSRDSInstance) PublishState(logger *log.Logger) error {
	logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-rds",
	}).WithFields(t.GetMetadata()).Debugf("PublishState: %#v", *t)
	return nil
}

// RefreshState -
func (t *AWSRDSInstance) RefreshState(logger *log.Logger) error {
	var AWSInputSession = session.Must(session.NewSession())
	assumedSession, err := AWSAssumeRole(t.AccountID, "ROLE_NAME", AWSInputSession)

	rdsClient := rds.New(
		assumedSession,
		&aws.Config{Region: aws.String(t.Region)},
	)
	output, err := rdsClient.DescribeDBInstances(
		&rds.DescribeDBInstancesInput{DBInstanceIdentifier: aws.String(t.ResourceID)},
	)

	if err != nil || len(output.DBInstances) < 1 {
		return err
	}

	t.DiskSpace = *output.DBInstances[0].AllocatedStorage
	t.InstanceClass = *output.DBInstances[0].DBInstanceClass
	t.InstanceStatus = *output.DBInstances[0].DBInstanceStatus
	t.PubliclyAccessible = *output.DBInstances[0].PubliclyAccessible

	input := &rds.ListTagsForResourceInput{ResourceName: &t.ResourceArn}
	result, err := rdsClient.ListTagsForResource(input)

	if err != nil {
		return err
	}

	t.Tags = make(map[string]string)
	for _, tag := range result.TagList {
		t.Tags[*tag.Key] = *tag.Value
	}

	return nil
}

// SendLogs -
func (t *AWSRDSInstance) SendLogs(logger *log.Logger) error {
	return nil
}

// SendMetrics -
func (t *AWSRDSInstance) SendMetrics(logger *log.Logger) error {
	return nil
}

// SendNotification -
func (t *AWSRDSInstance) SendNotification(logger *log.Logger) error {
	logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-rds",
	}).WithFields(t.GetMetadata()).Debugf("Notification send: %#v", *t)
	return nil
}

// TakeAction -
func (t *AWSRDSInstance) TakeAction(a Action, logger *log.Logger) error {
	logger.WithFields(logrus.Fields{
		"cloud-inquisitor-resource": "aws-rds",
	}).WithFields(t.GetMetadata()).Infof("taking action %#v on resource: %#v\n", a, *t)

	actionMode := settings.GetString("actions.mode")

	switch actionMode {
	case "dryrun":
		return nil
	case "normal":
		break
	default:
		return fmt.Errorf("Non-supported action mode: %v", actionMode)
	}

	assumedSession, err := AWSAssumeRole(t.AccountID, "ROLE_NAME", nil)
	if err != nil {
		return err
	}

	rdsClient := rds.New(
		assumedSession,
		&aws.Config{Region: aws.String(t.Region)},
	)

	switch a {
	case ACTION_PREVENT:
		// Stop RDS instance
		switch t.InstanceStatus {
		case "available":
			_, err := rdsClient.StopDBInstance(&rds.StopDBInstanceInput{
				DBInstanceIdentifier: aws.String(t.ResourceID)})

			if err != nil {
				return err
			}
		case "stopped":
			return nil

		}

	case ACTION_REMOVE:
		// Remove Deletion Protection
		_, err := rdsClient.ModifyDBInstance(&rds.ModifyDBInstanceInput{
			DBInstanceIdentifier: aws.String(t.ResourceID),
			DeletionProtection:   aws.Bool(false)})

		if err != nil {
			return err
		}

		timeFormat := settings.GetString("timestamp_format")

		dbSnapshotIdentifier := fmt.Sprintf(
			"cinq-snapshot-%s-%s",
			t.ResourceID,
			time.Now().UTC().Format(timeFormat),
		)

		// Create a final snapshot and delete RDS instance
		switch t.InstanceStatus {
		case "available", "stopped":
			_, err := rdsClient.DeleteDBInstance(
				&rds.DeleteDBInstanceInput{
					DBInstanceIdentifier:      aws.String(t.ResourceID),
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
func (t *AWSRDSInstance) GetType() Service {
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
