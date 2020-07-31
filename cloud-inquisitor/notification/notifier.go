package notification

import (
	"errors"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
)

type Notifier interface {
	SendNotification(Message) (string, error)
}

func NewNotifier() (Notifier, error) {
	if settings.IsSet("simple_email_service") {
		if settings.IsSet("simple_email_service.verified_email") {
			notifier := &AWSSESNotifier{}
			err := notifier.New()
			return notifier, err
		} else {
			return nil, errors.New("'simple_email_service' definition found in settings but no 'verified_email' provided")
		}
	}
	return nil, nil
}

type Message struct {
	Subject string
	Text    string
	HTML    string
	To      []string
	CC      []string
}

func NewHijackNotficationMessage(subject string, to, cc []string, content HijackNotificationContent) (Message, error) {
	html, err := NewHijackHTML(content)
	if err != nil {
		return Message{}, err
	}
	if html == "" {
		return Message{}, errors.New("html template is blank")
	}

	text, err := NewHijackText(content)
	if err != nil {
		return Message{}, err
	}
	if text == "" {
		return Message{}, errors.New("text template is blank")
	}

	return Message{
		Subject: subject,
		CC:      cc,
		To:      to,
		HTML:    html,
		Text:    text,
	}, nil
}
