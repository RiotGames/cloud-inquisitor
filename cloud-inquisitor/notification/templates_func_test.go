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
		PrimaryAccountId:    "12345678",
		HijackChain: []HijackChainElement{
			HijackChainElement{
				AccountId:              "abcdefg",
				Resource:               "public.test.bucket.com",
				ResourceType:           "route53",
				ResourceReferenced:     "test.bucket.com",
				ResourceReferencedType: "S3 Bucket",
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
