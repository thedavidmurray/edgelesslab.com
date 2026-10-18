#!/bin/bash
# Verify Gumroad product URLs are live before flipping website flags.
#
# Usage:
#   ./verify-url.sh https://edgelessai.gumroad.com/l/my-product
#   ./verify-url.sh urls.txt   (one URL per line)

set -euo pipefail

check_url() {
    local url="$1"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" -L "$url")

    if [ "$status" = "200" ]; then
        echo "LIVE ($status): $url"
        return 0
    else
        echo "NOT LIVE ($status): $url -- DO NOT flip comingSoon flag"
        return 1
    fi
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <url|file>"
    echo "  $0 https://edgelessai.gumroad.com/l/my-product"
    echo "  $0 urls.txt"
    exit 1
fi

failures=0

if [ -f "$1" ]; then
    # Read URLs from file
    while IFS= read -r url; do
        [ -z "$url" ] && continue
        [[ "$url" = \#* ]] && continue
        check_url "$url" || failures=$((failures + 1))
    done < "$1"
else
    # Single URL
    check_url "$1" || failures=$((failures + 1))
fi

if [ "$failures" -gt 0 ]; then
    echo ""
    echo "WARNING: $failures URL(s) not live. Do not update website."
    exit 1
else
    echo ""
    echo "All URLs verified live. Safe to update website."
fi
