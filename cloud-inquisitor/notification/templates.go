package notification

import (
	"bytes"
	"html/template"

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

func NewHijackHTML(content HijackNotificationContent) (string, error) {
	hijackHTMLTemplate, err := templateBox.FindString("hijack_template.html")
	if err != nil {
		return "", err
	}
	htmlBuffer := new(bytes.Buffer)
	t := template.Must(template.New("hijack-html").Parse(hijackHTMLTemplate))
	err = t.Execute(htmlBuffer, &content)
	if err != nil {
		return "", err
	}

	return htmlBuffer.String(), nil
}
