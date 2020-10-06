// +build functional

package notification

import (
	"testing"
)

func TestAWSSES(t *testing.T) {
	ses := &AWSSESNotifier{}
	err := ses.New()
	if err != nil {
		t.Fatal(err.Error())
	}

	if ses == nil {
		t.Fatal("SES notifier should not be nil")
	}

	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "123456789012",
		HijackChains: [][]HijackChainElement{
			[]HijackChainElement{
				HijackChainElement{
					AccountId:              "123456789012",
					Resource:               "public.test.bucket.com",
					ResourceType:           "route53",
				},
			},
		},
	}

	html, err := NewHijackHTML(content)
	if err != nil {
		t.Fatal(err.Error())
	}

	if html == "" {
		t.Fatal("html template should not be empty string")
	}
	
	text, err := NewHijackText(content)
	if err !+ nil {
		t.Fatal(err.Error())
	}
	
	if text == "" {
		t.Fatal("text template should not be empty string")
	}

	msg := Message{
		Subject: "CINQ Funcitonal Test",
		Text:    text,
		HTML:    html,
		To:      []string{ses.email},
		CC:      []string{},
	}

	id, err := ses.SendNotification(msg)

	if err != nil {
		t.Fatal(err.Error())
	}

	t.Log(id)
}
