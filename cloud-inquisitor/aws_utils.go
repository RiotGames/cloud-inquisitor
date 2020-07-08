package cloudinquisitor

import (
	"fmt"
	"strings"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sts"
)

// AWSAssumeRole - This function assumes a role in a target AWS Account and returns
// credential within the AssumeRole Output
// sess := session.Must(session.NewSession())
func AWSAssumeRole(accountID string, role string, inputSession *session.Session) (*session.Session, error) {
	if inputSession == nil {
		inputSession = session.Must(session.NewSession())
	}

	svc := sts.New(inputSession)
	arn := fmt.Sprintf("arn:aws:iam::%s:role/%s", accountID, role)
	input := &sts.AssumeRoleInput{
		RoleArn:         aws.String(arn),
		RoleSessionName: aws.String("default")}
	result, err := svc.AssumeRole(input)
	if err != nil {
		return nil, err
	}
	creds := credentials.NewStaticCredentials(
		*result.Credentials.AccessKeyId,
		*result.Credentials.SecretAccessKey,
		*result.Credentials.SessionToken,
	)
	assumedSession := session.Must(
		session.NewSession(&aws.Config{
			Credentials: creds}),
	)
	return assumedSession, nil
}

// KeysInMap compares the values in keyList against the Map Keys
// in a case insensitive way
func KeysInMap(m map[string]string, keyList []string) bool {
	lowerKeys := make([]string, len(keyList))
	for idx, key := range keyList {
		lowerKeys[idx] = strings.ToLower(key)
	}

	lowerMap := map[string]bool{}
	for key, _ := range m {
		lowerMap[strings.ToLower(key)] = true
	}

	for _, key := range lowerKeys {
		if _, ok := lowerMap[key]; !ok {
			fmt.Printf("key %v not in map %#v\n", key, lowerMap)
			return false
		}
	}

	return true
}
