package notification

import (
	"fmt"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/awserr"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ses"
)

type AWSSESNotifier struct {
	email string
	svc   *ses.SES
}

func (n *AWSSESNotifier) New() error {
	n.svc = ses.New(session.New())
	n.email = settings.GetString("simple_email_service.verified_email")

	return nil
}
func (n *AWSSESNotifier) SendNotification(msg Message) (string, error) {
	emailInput := &ses.SendEmailInput{
		Destination: &ses.Destination{
			ToAddresses: aws.StringSlice(msg.To),
			CcAddresses: aws.StringSlice(msg.CC),
		},
		Message: &ses.Message{
			Body: &ses.Body{
				Html: &ses.Content{
					Charset: aws.String("UTF-8"),
					Data:    aws.String(msg.HTML),
				},
				Text: &ses.Content{
					Charset: aws.String("UTF-8"),
					Data:    aws.String(msg.Text),
				},
			},
			Subject: &ses.Content{
				Charset: aws.String("UTF-8"),
				Data:    aws.String(msg.Subject),
			},
		},
		Source: aws.String(n.email),
	}

	result, err := n.svc.SendEmail(emailInput)
	if err != nil {
		if aerr, ok := err.(awserr.Error); ok {
			switch aerr.Code() {
			case ses.ErrCodeMessageRejected:
				return "", fmt.Errorf("failed to notify via SES. Error: %s: %s", ses.ErrCodeMessageRejected, aerr.Error())
			case ses.ErrCodeMailFromDomainNotVerifiedException:
				return "", fmt.Errorf("failed to notify via SES. Error: %s: %s", ses.ErrCodeMailFromDomainNotVerifiedException, aerr.Error())
			case ses.ErrCodeConfigurationSetDoesNotExistException:
				return "", fmt.Errorf("failed to notify via SES. Error: %s: %s", ses.ErrCodeConfigurationSetDoesNotExistException, aerr.Error())
			default:
				return "", fmt.Errorf("failed to notify via SES. Error: Generic: %s", aerr.Error())
			}
		} else {
			// Print the error, cast err to awserr.Error to get the Code and
			// Message from an error.
			return "", fmt.Errorf("failed to notify via SES. Error: Other: %s", err.Error())
		}
	}

	return *result.MessageId, nil
}
