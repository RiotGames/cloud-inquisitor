AVAILABLE_REGIONS = $(shell aws ec2 describe-regions | jq -r ".Regions[].RegionName")

AUDITORS = $(shell ls cloud-inquisitor/serverless)

.PHONY: providers_tf build

providers_tf: $(AVAILABLE_REGIONS)

provider_file:
	rm -f regions.tf && touch regions.tf

$(AVAILABLE_REGIONS): provider_file
	echo "provider \"aws\" {\n  alias  = \"$@\"\n  region = \"$@\"\n}\n\n" >> regions.tf

build: $(AUDITORS)

build_dir:
	mkdir -p builds

$(AUDITORS): build_dir
	GOARCH=amd64 GOOS=linux go build -o ./builds/$@ cloud-inquisitor/serverless/$@/*.go 	
