package notification

import (
	"reflect"
	"testing"

	"github.com/gobuffalo/packr"
)

func TestMessageGeneration(t *testing.T) {
	subject := "subject"
	to := []string{"toemail"}
	cc := []string{"ccemail"}

	msg, err := NewHijackNotficationMessage(subject, to, cc, HijackNotificationContent{})
	if err != nil {
		t.Fatal(err.Error())
	}

	if !reflect.DeepEqual(to, msg.To) {
		t.Fatal("to emails dont match")
	}

	if !reflect.DeepEqual(cc, msg.CC) {
		t.Fatal("cc emails dont match")
	}
}

func TestMessageNoChain(t *testing.T) {
	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "12345678",
		HijackChain:         []HijackChainElement{},
	}
	subject := "subject"
	to := []string{"toemail"}
	cc := []string{"ccemail"}
	msg, err := NewHijackNotficationMessage(subject, to, cc, content)
	if err != nil {
		t.Fatal(err.Error())
	}

	if !reflect.DeepEqual(to, msg.To) {
		t.Fatal("to emails dont match")
	}

	if !reflect.DeepEqual(cc, msg.CC) {
		t.Fatal("cc emails dont match")
	}

	testBox := packr.NewBox("./test_html")
	testHtml, err := testBox.FindString("hijack_test_no_chain.html")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testHtml != msg.HTML {
		t.Fatal("generated and test html do not match")
	}

	testBox = packr.NewBox("./test_text")
	testText, err := testBox.FindString("hijack_test_no_chain.txt")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testText != msg.Text {
		t.Fatal("generated and test text do not match")
	}
}

func TestMessageWithChain(t *testing.T) {
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
			HijackChainElement{
				AccountId:              "abcdefg",
				Resource:               "public.test.bucket.com",
				ResourceType:           "route53",
				ResourceReferenced:     "test.bucket.com",
				ResourceReferencedType: "S3 Bucket",
			},
		},
	}
	subject := "subject"
	to := []string{"toemail"}
	cc := []string{"ccemail"}
	msg, err := NewHijackNotficationMessage(subject, to, cc, content)
	if err != nil {
		t.Fatal(err.Error())
	}

	if !reflect.DeepEqual(to, msg.To) {
		t.Fatal("to emails dont match")
	}

	if !reflect.DeepEqual(cc, msg.CC) {
		t.Fatal("cc emails dont match")
	}

	testBox := packr.NewBox("./test_html")
	testHtml, err := testBox.FindString("hijack_test_with_chain.html")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testHtml != msg.HTML {
		t.Fatal("generated and test html do not match")
	}

	testBox = packr.NewBox("./test_text")
	testText, err := testBox.FindString("hijack_test_with_chain.txt")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testText != msg.Text {
		t.Fatal("generated and test text do not match")
	}
}
