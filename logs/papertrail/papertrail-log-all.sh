#!/bin/bash
# See https://github.com/papertrail/papertrail-cli
# Requires ahead of time:
# sudo gem install papertrail
# export PAPERTRAIL_API_TOKEN='YOURTOKEN'

papertrail --min-time 'July 4' --max-time 'today' > papertrail-log-all.log
papertrail --min-time 'July 4' --max-time 'today' --json > papertrail-log-all.json