package cloudinquisitor

import (
	"context"
	"encoding/json"
	"errors"
	"reflect"
	"time"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
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
	EventName       string
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
	EnvironmentId   string `json:"environmentId"`
	EnvironmentName string `json:"environmentName"`
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
	if err != nil {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "error getting regional session",
		}).WithFields(eb.GetMetadata()).Error(err.Error())

		return err
	}
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

	switch eb.EventName {
	case "TerminateEnvironment":
		return eb.refreshDeletedEnvironment(svc)
	case "CreateEnvironment":
		return eb.refreshCreatedEnvironment(svc)
	default:
		return errors.New("unkown elasticbeanstalk event to parse")
	}

	return nil

}

func (eb *AWSElasticBeanstalkEnvironmentResource) refreshDeletedEnvironment(svc *elasticbeanstalk.ElasticBeanstalk) error {
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

	eb.GetLogger().Debugf("describe environments input %#v", *input)
	eb.GetLogger().Debugf("describe environments result %#v", *result)

	var foundEnv *elasticbeanstalk.EnvironmentDescription = nil
	for _, env := range result.Environments {
		eb.GetLogger().Debugf("beanstalk environment: %#v", *env)
		if *env.EnvironmentId == eb.EnvironmentId {
			foundEnv = env
			break
		}
	}

	if foundEnv == nil {
		eb.logger.WithFields(logrus.Fields{
			"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
			"cloud-inquisitor-error":    "DescribeEnvironments",
		}).WithFields(eb.GetMetadata()).Error("could not find elasticbeanstalk environment")
		return errors.New("could not find elasticbeanstalk environment")
	}

	eb.Status = *foundEnv.Status
	eb.ApplicationName = *foundEnv.ApplicationName
	eb.CNAME = *foundEnv.CNAME
	eb.Endpoint = *foundEnv.EndpointURL
	eb.EnvironmentName = *foundEnv.EnvironmentName
	eb.CNAME = *foundEnv.CNAME

	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentResource) refreshCreatedEnvironment(svc *elasticbeanstalk.ElasticBeanstalk) error {
	input := &elasticbeanstalk.DescribeEnvironmentsInput{
		EnvironmentNames: []*string{
			aws.String(eb.EnvironmentName),
		},
		IncludeDeleted: aws.Bool(true),
	}

	isReady := false
	var foundEnv *elasticbeanstalk.EnvironmentDescription = nil
	for !isReady {

		result, err := svc.DescribeEnvironments(input)
		if err != nil {
			eb.logger.WithFields(logrus.Fields{
				"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
				"cloud-inquisitor-error":    "DescribeEnvironments",
			}).WithFields(eb.GetMetadata()).Error(err.Error())
			return err
		}

		eb.GetLogger().Debugf("describe environments input %#v", *input)
		eb.GetLogger().Debugf("describe environments result %#v", *result)

		for _, env := range result.Environments {
			eb.GetLogger().Debugf("beanstalk environment: %#v", *env)
			if *env.EnvironmentName == eb.EnvironmentName {
				foundEnv = env
				break
			}
		}

		if foundEnv == nil {
			eb.logger.WithFields(logrus.Fields{
				"cloud-inquisitor-resource": "aws-elasticbeanstalk-environment",
				"cloud-inquisitor-error":    "DescribeEnvironments",
			}).WithFields(eb.GetMetadata()).Error("could not find elasticbeanstalk environment")
			return errors.New("could not find elasticbeanstalk environment")
		}

		if *foundEnv.Status == "Ready" {
			break
		}

		foundEnv = nil
		time.Sleep(time.Second * 1)
	}

	eb.Status = *foundEnv.Status
	eb.ApplicationName = *foundEnv.ApplicationName
	eb.CNAME = *foundEnv.CNAME
	eb.Endpoint = *foundEnv.EndpointURL
	eb.EnvironmentName = *foundEnv.EnvironmentName
	eb.EnvironmentId = *foundEnv.EnvironmentId
	eb.CNAME = *foundEnv.CNAME

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
	// set account id first
	eb.AccountID = event.AccountID
	eb.Region = event.Region

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

	// set detail specific fields
	eb.logger.WithFields(eb.GetMetadata()).Debugf("aws event detail response elements: %#v", ebDetails.ResponseElements)
	eb.logger.WithFields(eb.GetMetadata()).Debugf("aws event detail request parameters: %#v", ebDetails.RequestParamaters)
	eb.EnvironmentId = ebDetails.RequestParamaters.EnvironmentId
	eb.EnvironmentName = ebDetails.RequestParamaters.EnvironmentName
	eb.EventName = ebDetails.EventName

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
		return errors.New("unable to marshal aws-elasticbeanstalk-environment resource")
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
	switch eb.EventName {
	case "TerminateEnvironment":
		return eb.publishDeletedEnvironment()
	case "CreateEnvironment":
		return eb.publishCreatedEnvironment()
	default:
		return errors.New("unknown elasticbeastalk event to publish")
	}
	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) publishCreatedEnvironment() error {
	db, err := graph.NewDBConnection()
	defer db.Close()
	if err != nil {
		eb.logger.WithFields(eb.GetMetadata()).Error(err.Error())
		return err
	}

	var account model.Account
	err = db.Where(model.Account{AccountID: eb.AccountID}).FirstOrCreate(&account).Error
	if err != nil {
		eb.GetLogger().Errorf("error getting account for elasticbeastalk %v: %v", eb.EnvironmentId, err.Error())
		return err
	}

	env := model.ElasticbeanstalkEnvironment{
		AccountID:       account.ID,
		ApplicationName: eb.ApplicationName,
		EnvironmentID:   eb.EnvironmentId,
		EnvironmentName: eb.EnvironmentName,
		EnvironmentURL:  eb.Endpoint,
		CName:           eb.CNAME,
		Region:          eb.Region,
	}
	err = db.Where(env).FirstOrCreate(&env).Error
	if err != nil {
		eb.GetLogger().Errorf("error creating elasticbeastalk environment  %v: %v", eb.EnvironmentId, err.Error())
		return err
	}

	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) publishDeletedEnvironment() error {
	db, err := graph.NewDBConnection()
	defer db.Close()
	if err != nil {
		eb.logger.WithFields(eb.GetMetadata()).Error(err.Error())
		return err
	}

	env := model.ElasticbeanstalkEnvironment{
		EnvironmentID:   eb.EnvironmentId,
		EnvironmentName: eb.EnvironmentName,
		ApplicationName: eb.ApplicationName,
		EnvironmentURL:  eb.Endpoint,
		CName:           eb.CNAME,
		Region:          eb.Region,
	}

	err = db.Delete(&env).Error
	if err != nil {
		eb.GetLogger().Errorf("error removing elasticbeanstalk %v: %v", eb.EnvironmentId, err.Error)
		return err
	}

	return nil
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) AnalyzeForHijack() (HijackChain, error) {
	switch eb.EventName {
	case "CreateEnvironment":
		return eb.analyzeCreatedEnvironment()
	case "TerminateEnvironment":
		return eb.analyzeTerminatedEnvironment()
	default:
		return HijackChain{}, errors.New("unknown elasticbeanstalk event to analyze for hijacks")
	}
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) analyzeCreatedEnvironment() (HijackChain, error) {
	return HijackChain{}, nil
}

func (eb *AWSElasticBeanstalkEnvironmentHijackableResource) analyzeTerminatedEnvironment() (HijackChain, error) {
	resolver, err := graph.NewResolver()
	if err != nil {
		eb.GetLogger().Errorf("error creating a new resolver to evaluate elasticbeanstalk hijacks: %v", err.Error())
		return HijackChain{}, err
	}

	ctx := context.Background()
	chain, err := resolver.Query().GetElasticbeanstalkUpstreamHijack(ctx, []string{eb.CNAME, eb.Endpoint})
	if err != nil {
		eb.GetLogger().Errorf("error querying graph for elasticbeanstalk hijack analysis: %v", err.Error())
	}

	hijacksChain := &HijackChain{Chain: make([]HijackChainElement, 0)}

	for _, link := range chain {
		hijacksChain.Chain = append(hijacksChain.Chain, HijackChainElement{
			AccountId:          link.Account,
			Resource:           link.ID,
			ResourceType:       link.Type.String(),
			ResourceReferenced: link.Value.ValueID,
		})
	}

	return *hijacksChain, nil
}
