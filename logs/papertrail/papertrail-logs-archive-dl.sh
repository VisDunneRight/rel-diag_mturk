curl -sH 'X-Papertrail-Token: YOURTOKEN' https://papertrailapp.com/api/v1/archives.json |
  grep -o '"filename":"[^"]*"' | egrep -o '[0-9-]+' |
  awk '$0 >= "2023-07-05" && $0 < "2023-07-10" {
    print "output " $0 ".tsv.gz"
    print "url https://papertrailapp.com/api/v1/archives/" $0 "/download"
  }' | curl --progress-bar -fLH 'X-Papertrail-Token: YOURTOKEN' -K-
