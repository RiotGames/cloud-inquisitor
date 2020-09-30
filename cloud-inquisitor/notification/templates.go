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

func GenerateContent(root *model.HijackableResourceRoot) HijackNotificationContent {
	content := HijackNotificationContent{
		PrimaryResource:     root.RootResource.Account,
		PrimaryAccountId:    root.RootResource.Account,
		PrimaryResourceType: root.RootResource.Type.String(),
	}

	chain := []HijackChainElement{}
	for _, element := range root.Maps {
		chain = append(chain, HijackChainElement{
			AccountId:              element.Resource.Account,
			Resource:               element.Resource.ID,
			ResourceType:           element.Resource.Type.String(),
			ResourceReferenced:     root.RootResource.ID,
			ResourceReferencedType: root.RootResource.Type.String(),
		})
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
