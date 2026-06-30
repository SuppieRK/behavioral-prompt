#!/bin/sh
if [ -z "$ACME_TEST_TOKEN" ]; then
  echo "ACME_TEST_TOKEN is required for integration validation" >&2
  exit 2
fi
echo "integration check would run here"
