package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"reflect"

	instrument "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/instrumentation"
	log "github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/logger"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/elasticbeanstalk"
	"github.com/sirupsen/logrus"
)

type AWSElasticBeanstalkEnvironmentResource struct {
	AccountID       string
	ApplicationName string
	EnvironmentName string
	EnvironmentId   string
	Region          string
	CNAME           string
	Endpoint        string
	Status          string
	logger          *log.Logger
}

type AWSElasticBeanstalkDetail struct {
	EventName         string                              `json:"eventName"`
	ErrorCode         string                              `json:"errorCode"`
	ErrorMessage      string                              `json:"errorMessage"`
	AWSRegion         string                              `json:"awsRegion"`
	RequestParamaters AWSElasticBeastalkRequestParameters `json:"requestParameters"`
	ResponseElements  AWSElasticBeanstalkResponseElement  `json:"responseElements"`
}

type AWSElasticBeastalkRequestParameters struct {
	EnvironmentId string `json:"environmentId"`
}
type AWSElasticBeanstalkResponseElement struct {
	/*Distribution struct {
		ID                 string `json:"id"`
		DomainName         string `json:"domainName"`
		Status             string `json:"status"`
		DistributionConfig struct {
			Origins struct {
				Items []struct {
					DomainName string `json:"domainName"`
					ID         string `json:"id"`
				} `json:"items"`
			} `json:"origins"`
			OriginGroups struct {
				Items []struct {
					ID      string `json:"id"`
					Members struct {
						Items []struct {
							OriginID string `json:"originId"`
						} `json:"items"`
					} `json:"members"`
				} `json:"items"`
			} `json:"originGroups"`
		} `json:"distributionConfig"`
	} `json:"distribution"`*/
}

func (eb *AWSElasticBeanstalkEnvironmentResource) RefreshState() error {
	if !settings.IsSet("assume_role") {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "missing settings value",
		}).WithFields(eb.GetMetadata()).Error(errors.New("settings value assume_role not set"))
		return errors.New("settings value assume_role not set")
	}
	accountSession, err := AWSAssumeRole(eb.AccountID, settings.GetString("assume_role"), session.New())
	regionalSession := accountSession.Copy(&aws.Config{
		Region: aws.String(eb.Region),
	})
	if err != nil {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "assume role error",
		}).WithFields(eb.GetMetadata()).Error(err.Error())
		return err
	}

	svc := elasticbeanstalk.New(regionalSession)
	input := &elasticbeanstalk.DescribeEnvironmentsInput{
		EnvironmentIds: []*string{
			aws.String(eb.EnvironmentId),
		},
		IncludeDeleted: aws.Bool(true),
	}

	result, err := svc.DescribeEnvironments(input)
	if err != nil {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "DescribeEnvironments",
		}).WithFields(eb.GetMetadata()).Error(err.Error())
		return err
	}

	var foundEnv *elasticbeanstalk.EnvironmentDescription = nil
	for _, env := range result.Environments {
		if *env.EnvironmentId == eb.EnvironmentId {
			foundEnv = env
			break
		}
	}

	eb.Status = *foundEnv.Status
	eb.ApplicationName = *foundEnv.ApplicationName
	eb.CNAME = *foundEnv.CNAME
	eb.Endpoint = *foundEnv.EndpointURL
	eb.EnvironmentName = *foundEnv.EnvironmentName

	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentResource) SendNotification() error {
	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentResource) GetType() string {
	return SERVICE_AWS_ELASTICBEANSTALK
}

func (eb *AWSElasticBeanstalkEnvironmentResource) GetMetadata() map[string]interface{} {
	return map[string]interface{}{
		"account":          eb.AccountID,
		"application-name": eb.ApplicationName,
		"enviornment-name": eb.EnvironmentName,
		"environment-id":   eb.EnvironmentId,
		"cname":            eb.CNAME,
		"endpoint":         eb.Endpoint,
		"status":           eb.Status,
		"serviceType":      eb.GetType(),
	}
}

func (eb *AWSElasticBeanstalkEnvironmentResource) GetLogger() *log.Logger {
	return eb.logger
}

type AWSElasticBeanstalkEnvironmentHijackableResource struct {
	AWSElasticBeanstalkEnvironmentResource
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) NewFromEventBus(event events.CloudWatchEvent, ctx context.Context, passedInMetadata map[string]interface{}) error {
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
	logger := instrument.GetInstrumentedLogger(opts, ctx)
	eb.logger = logger

	var ebDetails AWSElasticBeanstalkDetail
	err = json.Unmarshal(event.Detail, &ebDetails)
	if err != nil {
		eb.logger.Error(err.Error(), nil)
		return err
	}

	if ebDetails.ErrorCode != "" {
		return errors.New(ebDetails.ErrorMessage)
	}

	if reflect.DeepEqual(ebDetails.ResponseElements, (AWSElasticBeanstalkResponseElement{})) {
		// this is a current known issue with elasticbeanstalk with a suppor ticket in place
		//return errors.New("response element of cloudfront distribution is missing")
	}

	eb.logger.WithFields(eb.GetMetadata()).Debugf("aws event detail response elements: %#v", ebDetails.ResponseElements)

	eb.EnvironmentId = ebDetails.RequestParamaters.EnvironmentId
	eb.Region = ebDetails.AWSRegion

	err = eb.RefreshState()
	if err != nil {
		eb.logger.Error(err.Error(), nil)
		return err
	}

	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) NewFromPassableResource(resource PassableResource, ctx context.Context, passedInMetadata map[string]interface{}) error {
	lamdbaMetadata, err := LambdaMetadataFromPassableResource(ctx, resource)
	if err != nil {
		return err
	}

	mergedMetaData := map[string]interface{}{}
	for k, v := range passedInMetadata {
		mergedMetaData[k] = v
	}
	for k, v := range lamdbaMetadata {
		mergedMetaData[k] = v
	}
	opts := log.LoggerOpts{
		Level:    log.LogrusLevelConv(settings.GetString("log_level")),
		Metadata: mergedMetaData,
	}
	eb.logger = instrument.GetInstrumentedLogger(opts, ctx)
	structJson, err := json.Marshal(resource.Resource)
	if err != nil {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "json marshal error",
		}).WithFields(eb.GetMetadata()).Error(err.Error(), nil)
		return errors.New("unable to marshal aws-route53-record-set resource")
	}

	err = json.Unmarshal(structJson, eb)
	if err != nil {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "json unmarshal error",
		}).WithFields(eb.GetMetadata()).Error(err.Error(), nil)
		return errors.New("unable to unmarshal aws-elasticbeanstalk-environment resource")
	}

	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) PublishState() error {
	return nil
}
