package cloudinquisitor

type AWSResourceMetadata struct {
	AccountID       string `json:"AccountID" mapstructure:"AccountID"`
	Region          string `json:"Region" mapstructure:"Region"`
	ResourceARN     string `json:"ResourceARN" mapstructure:"ResourceARN"`
	ResourceID      string `json:"ResourceID" mapstructure:"ResourceID"`
	ResourceName    string `json:"ResourceName" mapstructure:"ResourceName"`
	ResourceType    string `json:"ResourceType" mapstructure:"ResourceType"`
	ResourceSubType string `json:"ResourceSubType" mapstructure:"ResourceSubType"`
}
