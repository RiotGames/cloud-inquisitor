package notification

import (
	//"io/ioutil"
	"testing"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
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
		HijackChains:        [][]HijackChainElement{},
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
		HijackChains: [][]HijackChainElement{
			[]HijackChainElement{
				HijackChainElement{
					AccountId:    "123456789012",
					Resource:     "public.test.bucket.com",
					ResourceType: "route53",
				},
				HijackChainElement{
					AccountId:    "123456789012",
					Resource:     "public.test.bucket.com",
					ResourceType: "route53",
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
		HijackChains:        [][]HijackChainElement{},
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
		HijackChains: [][]HijackChainElement{
			[]HijackChainElement{
				HijackChainElement{
					AccountId:    "123456789012",
					Resource:     "public.test.bucket.com",
					ResourceType: "route53",
				},
				HijackChainElement{
					AccountId:    "123456789012",
					Resource:     "public.test.bucket.com",
					ResourceType: "route53",
				},
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

/*
AccountId:              rawChain.Resource.Account,
		Resource:               rawChain.Resource.ID,
		ResourceType:           rawChain.Resource.Type.String(),
		ResourceReferenced:     "",
		ResourceReferencedType: "",
*/
func TestGenerateContent(t *testing.T) {
	chain := &model.HijackableResourceRoot{
		ID: "testID",
		RootResource: &model.HijackableResource{
			ID:      "test root resource",
			Account: "test root account",
			Type:    model.TypeElasticbeanstalk,
		},
		Direction: model.DirectionDownstream,
		Maps: []*model.HijackableResource{
			&model.HijackableResource{
				ID:      "test downstream",
				Account: "test downstream account",
				Type:    model.TypeElasticbeanstalk,
			},
		},
	}

	content := GenerateContent(chain)
	t.Logf("content struct %#v", content)
}
