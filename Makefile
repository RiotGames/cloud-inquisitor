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

build: clean generate $(AUDITORS)

build_dir:
	mkdir -p builds

$(AUDITORS): build_dir
	mkdir -p ./builds/$@
	GOARCH=amd64 GOOS=linux go build -o ./builds/$@/$@ cloud-inquisitor/serverless/$@/*.go
	cp  $(SETTINGS_FILE) ./builds/$@/settings.json
	cd ./builds/$@ && zip ../$@.zip ./*

build_cli:
	go build -o ./cinqctl cmd/*.go

generate:
	cd cloud-inquisitor/graph && go run github.com/99designs/gqlgen generate
