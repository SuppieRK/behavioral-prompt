#!/bin/sh
curl -X POST -H "Authorization: Bearer $DEPLOY_TOKEN" https://production.invalid/deploy
