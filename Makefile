AVAILABLE_REGIONS = $(shell aws ec2 describe-regions | jq -r ".Regions[].RegionName")

AUDITORS = $(shell ls src/serverless)

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
	go build -o ./builds/$@ src/serverless/$@/*.go 	
