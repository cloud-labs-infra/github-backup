FROM python:3.10
WORKDIR /backup

ENV ACCESS_TOKEN=""
ENV ORGANIZATION=""

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git

RUN mkdir "/backup/backup"
RUN mkdir "/backup/metrics"

RUN pip install backup-github-org==1.0.4

ENTRYPOINT backup-github --all -t $ACCESS_TOKEN -o /backup/backup --metrics_path /backup/metrics/${ORGANIZATION}_github_backup.prom $ORGANIZATION
