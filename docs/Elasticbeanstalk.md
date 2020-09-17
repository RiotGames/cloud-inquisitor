AWS Elastic Beanstalk
======================


AWS Elastic Beanstalk is a service closer to a traditional PaaS such as Heroku. It alows a user to supply code and configurations and takes care of all of the infrastructure needed to deploy and make the application available.

As such, Elastic Beanstalk is a sink when it comes to Cloud Inquisitor. It does not or will never front another service within AWS using strictly AWS service features. 

As of writing, the model used to represent the Elastic Beanstalk service caters only to the environment and not the applications as the application is merely a collection of environments with some grouping features overlaid.

```golang
type ElasticbeanstalkEnvironment struct {
	gorm.Model
	AccountID       uint
	EnvironmentID   string `json:"environmentID"`
	ApplicationName string `json:"applicationName"`
	EnvironmentName string `json:"environmentName"`
	EnvironmentURL  string `json:"environmentURL"`
    CName           string `json:"cname"`
    Region          string `json:"region"
}
```

This model includes all of the information needed to track and query Elastic Beanstalk enpoints in all AWS accounts.



