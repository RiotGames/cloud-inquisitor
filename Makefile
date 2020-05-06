AVAILABLE_REGIONS = $(shell aws ec2 describe-regions | jq -r ".Regions[].RegionName")

.PHONY: providers_tf

providers_tf: $(AVAILABLE_REGIONS)

provider_file:
	rm -f regions.tf && touch regions.tf

$(AVAILABLE_REGIONS): provider_file
	echo "provider \"aws\" {\n  alias  = \"$@\"\n  region = \"$@\"\n}\n\n" >> regions.tf