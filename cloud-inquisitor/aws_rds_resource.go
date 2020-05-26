package cloudinquisitor

import (
	"fmt"
	"log"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/rds"
)

// AWSRDSInstance - AWS RDS Instance
type AWSRDSInstance struct {
	State        int
	AccountID    string
	Region       string
	ResourceID   string
	ResourceType string

	DiskSpace          int64
	Engine             string
	InstanceClass      string
	InstanceStatus     string
	PubliclyAccessible bool
}

// Audit : AWS RDS Instance Audit
func (t *AWSRDSInstance) Audit() (Action, error) {
	var result Action

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

// PublishState -
func (t *AWSRDSInstance) PublishState() error {
	log.Printf("PublishState: %#v\n", *t)
	return nil
}

// RefreshState -
func (t *AWSRDSInstance) RefreshState() error {
	var AWSInputSession = session.Must(session.NewSession())
	assumedSession, err := AWSAssumeRole(t.AccountID, "ROLE_NAME", AWSInputSession)

	rdsClient := rds.New(
		assumedSession,
		&aws.Config{Region: aws.String(t.Region)},
	)
	output, err := rdsClient.DescribeDBInstances(
		&rds.DescribeDBInstancesInput{DBInstanceIdentifier: aws.String(t.ResourceID)},
	)

	if err != nil {
		return err
	}

	t.DiskSpace = *output.DBInstances[0].AllocatedStorage
	t.InstanceClass = *output.DBInstances[0].DBInstanceClass
	t.InstanceStatus = *output.DBInstances[0].DBInstanceStatus
	t.PubliclyAccessible = *output.DBInstances[0].PubliclyAccessible

	return nil
}

// SendLogs -
func (t *AWSRDSInstance) SendLogs() error {
	return nil
}

// SendMetrics -
func (t *AWSRDSInstance) SendMetrics() error {
	return nil
}

// SendNotification -
func (t *AWSRDSInstance) SendNotification() error {
	log.Printf("Notification send: %#v\n", *t)
	return nil
}

// TakeAction -
func (t *AWSRDSInstance) TakeAction(a Action) error {
	log.Printf("taking action %#v on resource: %#v\n", a, *t)

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

		timeFormat, err := GetConfig("time_format")
		if err != nil {
			return err
		}

		dbSnapshotIdentifier := fmt.Sprintf(
			"cinq-snapshot-%s-%s",
			t.ResourceID,
			time.Now().UTC().Format(timeFormat),
		)

		// Create a final snapshot and delete RDS instance
		switch t.InstanceStatus {
		case "available":
			fallthrough
		case "stopped":
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
