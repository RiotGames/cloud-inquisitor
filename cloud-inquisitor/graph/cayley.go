package graph

import (
	"errors"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/secrets/vault"
	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"github.com/cayleygraph/cayley"
	"github.com/cayleygraph/cayley/graph"
	_ "github.com/cayleygraph/cayley/graph/sql/mysql"
	"github.com/cayleygraph/quad"
)

var intialized bool = false

type Graph struct {
	client *cayley.Handle
}

func NewGraph() (*Graph, error) {
	if settings.IsSet("cayley") {
		var connectionString string
		var err error = nil
		switch settings.GetString("cayley.connection_string.type") {
		case "vault":
			connectionString, err = vault.GetString(settings.GetString("cayley.connection_string.value"), "value")
			if err != nil {
				return nil, err
			}
		case "string":
			connectionString = settings.GetString("cayley.connection_string.value")
		default:
			return nil, errors.New("unknown datastore/graph configuration type")
		}

		if !intialized {
			graph.InitQuadStore(settings.GetString("cayley.database_type"), connectionString, nil)
		}

		g, err := cayley.NewGraph(settings.GetString("cayley.database_type"), connectionString, nil)
		return &Graph{g}, err
	} else {
		return nil, errors.New("no configuration for a graph store found")
	}
}

func (g *Graph) AddQuad(subject, predicate, object interface{}) error {
	return g.client.AddQuad(quad.Make(subject, predicate, object, nil))
}
