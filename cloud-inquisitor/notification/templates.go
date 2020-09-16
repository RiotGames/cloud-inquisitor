package notification

import (
	"bytes"
	"html/template"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/graph/model"
	"github.com/gobuffalo/packr"
)

var templateBox packr.Box

func init() {
	templateBox = packr.NewBox("./templates")
}

type HijackChainElement struct {
	AccountId              string
	Resource               string
	ResourceType           string
	ResourceReferenced     string
	ResourceReferencedType string
}

type HijackNotificationContent struct {
	PrimaryResource     string
	PrimaryResourceType string
	PrimaryAccountId    string
	HijackChain         []HijackChainElement
}

func GenerateContent(rawChain *model.HijackableResourceChain) HijackNotificationContent {
	content := HijackNotificationContent{
		PrimaryResource:     rawChain.Resource.ID,
		PrimaryAccountId:    rawChain.Resource.Account,
		PrimaryResourceType: rawChain.Resource.Type.String(),
	}

	chain := []HijackChainElement{}
	for idx, resource := range rawChain.Upstream {
		if idx == len(rawChain.Upstream)-1 {
			chain = append(chain, HijackChainElement{
				AccountId:              resource.Account,
				Resource:               resource.ID,
				ResourceType:           resource.Type.String(),
				ResourceReferenced:     rawChain.Resource.ID,
				ResourceReferencedType: rawChain.Resource.Type.String(),
			})
		} else {
			chain = append(chain, HijackChainElement{
				AccountId:              resource.Account,
				Resource:               resource.ID,
				ResourceType:           resource.Type.String(),
				ResourceReferenced:     rawChain.Upstream[idx+1].ID,
				ResourceReferencedType: rawChain.Upstream[idx+1].Type.String(),
			})
		}
	}

	if len(rawChain.Downstream) == 0 {
		chain = append(chain, HijackChainElement{
			AccountId:              rawChain.Resource.Account,
			Resource:               rawChain.Resource.ID,
			ResourceType:           rawChain.Resource.Type.String(),
			ResourceReferenced:     "not applicable",
			ResourceReferencedType: "not applicable",
		})
	} else {
		chain = append(chain, HijackChainElement{
			AccountId:              rawChain.Resource.Account,
			Resource:               rawChain.Resource.ID,
			ResourceType:           rawChain.Resource.Type.String(),
			ResourceReferenced:     rawChain.Downstream[0].ID,
			ResourceReferencedType: rawChain.Downstream[0].Type.String(),
		})
	}

	for idx, resource := range rawChain.Downstream {
		if idx == len(rawChain.Downstream)-1 {
			chain = append(chain, HijackChainElement{
				AccountId:              resource.Account,
				Resource:               resource.ID,
				ResourceType:           resource.Type.String(),
				ResourceReferenced:     "not applicable",
				ResourceReferencedType: "not applicable",
			})
		} else {
			chain = append(chain, HijackChainElement{
				AccountId:              resource.Account,
				Resource:               resource.ID,
				ResourceType:           resource.Type.String(),
				ResourceReferenced:     rawChain.Downstream[idx+1].ID,
				ResourceReferencedType: rawChain.Downstream[idx+1].Type.String(),
			})
		}
	}

	content.HijackChain = chain

	return content
}

func NewHijackHTML(content HijackNotificationContent) (string, error) {
	funcMap := map[string]interface{}{
		"isEven": func(val int) bool {
			return val%2 == 0
		},
	}
	hijackHTMLTemplate, err := templateBox.FindString("hijack_template.html")
	if err != nil {
		return "", err
	}
	htmlBuffer := new(bytes.Buffer)
	t := template.Must(template.New("hijack-html").Funcs(funcMap).Parse(hijackHTMLTemplate))
	err = t.Execute(htmlBuffer, &content)
	if err != nil {
		return "", err
	}

	return htmlBuffer.String(), nil
}

func NewHijackText(content HijackNotificationContent) (string, error) {
	hijackTextTemplate, err := templateBox.FindString("hijack_template.txt")
	if err != nil {
		return "", err
	}

	textBuffer := new(bytes.Buffer)
	t := template.Must(template.New("hijack-text").Parse(hijackTextTemplate))
	err = t.Execute(textBuffer, &content)
	if err != nil {
		return "", err
	}

	return textBuffer.String(), nil
}
