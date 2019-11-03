#!/bin/sh

# Update version number from https://schema.org/docs/releases.html
curl -L -f -o schema.jsonld http://schema.org/version/5.0/schema.jsonld
# Apache License 2.0 https://github.com/schemaorg/schemaorg/blob/v5.0-release/LICENSE

curl -L -f -o ro-crate.jsonld https://w3id.org/ro/crate/0.3-DRAFT/context
# CC0  https://creativecommons.org/publicdomain/zero/1.0/
