FROM python:3.10
WORKDIR /backup
RUN pip install backup-github-org==1.0.4
ENTRYPOINT ["/usr/local/bin/backup-github", "--all", "-t", "$ACCESS_TOKEN", "-o", "./backup/",
  "--metrics_path", "./metrics/${ORGANIZATION}_github_backup.prom", "$ORGANIZATION", ">", "./logs_${ORGANIZATION}.log"]
