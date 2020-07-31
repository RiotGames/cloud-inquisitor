package notification

import (
	//"io/ioutil"
	"testing"

	"github.com/gobuffalo/packr"
)

func TestHijackTemplateExists(t *testing.T) {
	_, err := templateBox.FindString("hijack_template.html")
	if err != nil {
		t.Fatal(err.Error())
	}

	_, err = templateBox.FindString("hijack_template.txt")
	if err != nil {
		t.Fatal(err.Error())
	}
}

func TestHijackHTMLNoChain(t *testing.T) {
	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "123456789012",
		HijackChain:         []HijackChainElement{},
	}

	html, err := NewHijackHTML(content)
	if err != nil {
		t.Fatal(err.Error())
	}

	if html == "" {
		t.Fatal("html template should not be empty string")
	}

	//ioutil.WriteFile("./test_html/hijack_test_no_chain.html", []byte(html), 0755)
	testBox := packr.NewBox("./test_html")
	testHtml, err := testBox.FindString("hijack_test_no_chain.html")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testHtml != html {
		t.Fatal("generated and test html do not match")
	}
}

func TestHijackHTMLWithChain(t *testing.T) {
	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "123456789012",
		HijackChain: []HijackChainElement{
			HijackChainElement{
				AccountId:              "123456789012",
				Resource:               "public.test.bucket.com",
				ResourceType:           "route53",
				ResourceReferenced:     "test.bucket.com",
				ResourceReferencedType: "S3 Bucket",
			},
			HijackChainElement{
				AccountId:              "123456789012",
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

	//ioutil.WriteFile("./test_html/hijack_test_with_chain.html", []byte(html), 0755)
	testBox := packr.NewBox("./test_html")
	testHtml, err := testBox.FindString("hijack_test_with_chain.html")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testHtml != html {
		t.Fatal("generated and test html do not match")
	}
}

func TestHijackTextNoChain(t *testing.T) {
	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "123456789012",
		HijackChain:         []HijackChainElement{},
	}

	text, err := NewHijackText(content)
	if err != nil {
		t.Fatal(err.Error())
	}

	if text == "" {
		t.Fatal("text template should not be empty string")
	}

	//ioutil.WriteFile("./test_text/hijack_test_no_chain.txt", []byte(text), 0755)
	testBox := packr.NewBox("./test_text")
	testText, err := testBox.FindString("hijack_test_no_chain.txt")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testText != text {
		t.Fatal("generated and test text do not match")
	}
}

func TestHijackTextWithChain(t *testing.T) {
	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "123456789012",
		HijackChain: []HijackChainElement{
			HijackChainElement{
				AccountId:              "123456789012",
				Resource:               "public.test.bucket.com",
				ResourceType:           "route53",
				ResourceReferenced:     "test.bucket.com",
				ResourceReferencedType: "S3 Bucket",
			},
			HijackChainElement{
				AccountId:              "123456789012",
				Resource:               "public.test.bucket.com",
				ResourceType:           "route53",
				ResourceReferenced:     "test.bucket.com",
				ResourceReferencedType: "S3 Bucket",
			},
		},
	}

	text, err := NewHijackText(content)
	if err != nil {
		t.Fatal(err.Error())
	}

	if text == "" {
		t.Fatal("text template should not be empty string")
	}

	//ioutil.WriteFile("./test_text/hijack_test_with_chain.txt", []byte(text), 0755)
	testBox := packr.NewBox("./test_text")
	testText, err := testBox.FindString("hijack_test_with_chain.txt")
	if err != nil {
		t.Fatal(err.Error())
	}

	if testText != text {
		t.Fatal("generated and test text do not match")
	}
}
