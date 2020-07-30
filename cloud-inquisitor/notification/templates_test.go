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
}

func TestHijackHTMLNoChain(t *testing.T) {
	content := HijackNotificationContent{
		PrimaryResource:     "test.bucket.com",
		PrimaryResourceType: "S3 Bucket",
		PrimaryAccountId:    "12345678",
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
