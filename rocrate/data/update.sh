#!/bin/sh

# Update version number from https://schema.org/docs/releases.html
curl -L -f -o schema.jsonld https://schema.org/version/10.0/schemaorg-all-http.jsonld
# Apache License 2.0 https://github.com/schemaorg/schemaorg/blob/V10.0-release/LICENSE
# no NOTICE - so just keeping file as-is is sufficient (we are also Apache-2.0)

curl -L -f -o ro-crate.jsonld https://w3id.org/ro/crate/1.1/context
# CC0  https://creativecommons.org/publicdomain/zero/1.0/
# so no attribution needed
