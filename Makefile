AVAILABLE_REGIONS = $(shell aws ec2 describe-regions | jq -r ".Regions[].RegionName")
AUDITORS = $(shell ls cloud-inquisitor/serverless)
SETTINGS_FILE ?= ./settings.json

.PHONY: providers_tf build

clean:
	rm -rf builds
	rm -rf terraform_modules/step_function/lambda_zips

providers_tf: $(AVAILABLE_REGIONS)

provider_file:
	rm -f regions.tf && touch regions.tf

$(AVAILABLE_REGIONS): provider_file
	echo "provider \"aws\" {\n  alias  = \"$@\"\n  region = \"$@\"\n}\n\n" >> regions.tf

generate:
	cd cloud-inquisitor/graph && go run github.com/99designs/gqlgen generate

packr_dep:
	go get -u github.com/gobuffalo/packr/packr

packr_generate: packr_dep
	$(shell go env GOPATH)/bin/packr
	
packr_clean: packr_dep
	$(shell go env GOPATH)/bin/packr clean

build: clean generate packr_generate $(AUDITORS) packr_clean

build_dir:
	mkdir -p builds

$(AUDITORS): build_dir
	mkdir -p ./builds/$@
	GOARCH=amd64 GOOS=linux go build -o ./builds/$@/$@ cloud-inquisitor/serverless/$@/*.go
	cp  $(SETTINGS_FILE) ./builds/$@/settings.json
	cd ./builds/$@ && zip ../$@.zip ./*

build_cli: generate
	go build -o ./cinqctl cmd/*.go

deploy:
	terraform apply

destroy:
	terraform destroy
