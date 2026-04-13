#!/bin/bash
# Regenerate Packages index from debs/ directory
set -euo pipefail
cd "$(dirname "$0")"
dpkg-scanpackages debs /dev/null > Packages 2>/dev/null
bzip2 -fk Packages
gzip -fk Packages
echo "Updated Packages index ($(grep -c '^Package:' Packages) packages)"
