package notification

import (
	"reflect"
	"testing"
)

func TestMessageGeneration(t *testing.T) {
	subject := "subject"
	to := []string{"toemail"}
	cc := []string{"ccemail"}

	msg := NewHijackNotficationMessage(subject, to, cc)

	if !reflect.DeepEqual(to, msg.To) {
		t.Fatal("to emails dont match")
	}

	if !reflect.DeepEqual(cc, msg.CC) {
		t.Fatal("cc emails dont match")
	}
}
