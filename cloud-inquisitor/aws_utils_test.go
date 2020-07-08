package cloudinquisitor

import (
	"testing"
)

func TestKeysInMap(t *testing.T) {
	m1 := map[string]string{
		"A":   "a",
		"b":   "b",
		"Cat": "cat",
	}

	l1 := []string{"a", "b", "CAT"}

	if !KeysInMap(m1, l1) {
		t.Fatalf("keys in list %#v are not in map %#v\n", l1, m1)
	}
}
