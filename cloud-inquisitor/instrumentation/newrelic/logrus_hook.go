package newrelic

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

var DefaultNewRelicHookOpts NewRelicHookOpts

func init() {
	DefaultNewRelicHookOpts = NewRelicHookOpts{
		URL: "https://log-api.newrelic.com/log/v1",
	}
}

type NewRelicHookOpts struct {
	URL             string
	License         string
	ApplicationName string
}

type NewRelicHook struct {
	newRelickHookOpts NewRelicHookOpts
	httpClient        *http.Client
	formatter         *NewRelicHookFormatter
}

func NewNewRelicHook(opts NewRelicHookOpts) *NewRelicHook {
	dialer := &net.Dialer{
		Timeout: 10 * time.Second,
	}

	transport := &http.Transport{
		Dial:                dialer.Dial,
		TLSHandshakeTimeout: 5 * time.Second,
	}

	httpClient := &http.Client{
		Timeout:   15 * time.Second,
		Transport: transport,
	}

	return &NewRelicHook{
		httpClient:        httpClient,
		newRelickHookOpts: opts,
		formatter:         &NewRelicHookFormatter{},
	}
}

func (nrh *NewRelicHook) Levels() []logrus.Level {
	return logrus.AllLevels
}

func (nrh *NewRelicHook) Fire(entry *logrus.Entry) error {
	if nrh.httpClient == nil {
		return errors.New("New Relic Logrus Hook Error: no http client defined")
	}

	if nrh.newRelickHookOpts.URL == "" {
		return errors.New("New Relic Logrus Hook Error: New Relic endpoint not set in settings (newrelic.endpoint)")
	}

	if nrh.newRelickHookOpts.License == "" {
		return errors.New("New Relic Logrus Hook Error: New Relic license not set in settings (newrelic.license)")
	}

	logBytes, err := nrh.formatter.Format(entry, nrh.newRelickHookOpts)

	if err != nil {
		return errors.New(fmt.Sprintf("New Relic Logrus Hook: recieved error from formatter - %v", err.Error()))
	}

	logRequest, err := http.NewRequest("POST", nrh.newRelickHookOpts.URL, bytes.NewBuffer(logBytes))
	if err != nil {
		return errors.New(fmt.Sprintf("New Relic Logrus Hook Error: Error creating new request - %v", err.Error()))
	}
	logRequest.Header.Set("Content-Type", "application/json")
	logRequest.Header.Set("X-License-Key", nrh.newRelickHookOpts.License)

	fmt.Printf("sending logrus hook json: %v\n", string(logBytes))
	resp, err := nrh.httpClient.Do(logRequest)

	fmt.Println("logrus hook response code: ", resp.StatusCode)
	if body, bodyerr := ioutil.ReadAll(resp.Body); bodyerr == nil {
		fmt.Println("logurs hook response body: ", string(body))
	} else {
		fmt.Println("error reading body: ", bodyerr.Error())
	}
	resp.Body.Close()

	if err != nil {
		return errors.New(fmt.Sprintf("New Relic Logrus Hook: recieved error posting log - %v", err.Error()))
	}

	return nil
}

type NewRelicHookFormatter struct{}

// Format will format a logrus.Entry in the following way:
//   timestamp will be in time.Unix() (seconds since epoch)
//   JSON format will follow the New Relic Detailed JSON body message
//     https://docs.newrelic.com/docs/logs/new-relic-logs/log-api/introduction-log-api#message-attribute-parsin
//   Common fields include:
//     - application_name: settings.name
//     - log_level: settings.log_level
//
//   Per Log Fields include:
//     - Workflow UUID
//     - Session UUID
//     - Fields included in the WithFields logger call
func (nrhf *NewRelicHookFormatter) Format(entry *logrus.Entry, opts NewRelicHookOpts) ([]byte, error) {
	//time in seconds
	timestamps := entry.Time.Unix()

	// json common entry
	commonEntry := map[string]interface{}{}
	commonEntry["timestamp"] = timestamps
	commonAttributes := map[string]interface{}{}
	commonAttributes["log_level"] = entry.Level
	commonAttributes["application_name"] = opts.ApplicationName
	commonEntry["attributes"] = commonAttributes

	// json log entry
	logEntry := map[string]interface{}{}
	logEntry["timestamp"] = timestamps
	logEntry["message"] = entry.Message

	logAttributes := map[string]interface{}{}
	for k, v := range entry.Data {
		switch v := v.(type) {
		case error:
			logAttributes[removeWhiteSpace(k)] = v.Error()
		default:
			logAttributes[removeWhiteSpace(k)] = v
		}
	}

	if entry.HasCaller() {
		funcVal := entry.Caller.Function
		fileVal := fmt.Sprintf("%s:%d", entry.Caller.File, entry.Caller.Line)
		logAttributes["func"] = funcVal
		logAttributes["file"] = fileVal
	}

	logEntry["attributes"] = logAttributes

	jsonEntry := map[string]interface{}{
		"common": commonEntry,
		"logs": []map[string]interface{}{
			logEntry,
		},
	}

	jsonBytes, err := json.Marshal([]map[string]interface{}{jsonEntry})
	if err != nil {
		hookError := errors.New(fmt.Sprintf("New Relic Logrus Hook: recieved error from formatter - %v", err.Error()))
		return jsonBytes, hookError
	}
	return jsonBytes, err
}

func removeWhiteSpace(whitespacestring string) string {
	initialStrings := strings.Split(strings.TrimSpace(whitespacestring), " ")
	finalStringComponents := make([]string, len(initialStrings))

	for idx, stringComponent := range initialStrings {
		switch idx {
		case 0:
			finalStringComponents[idx] = stringComponent
		default:
			finalStringComponents[idx] = strings.Title(stringComponent)
		}
	}

	return strings.Join(finalStringComponents, "")
}
