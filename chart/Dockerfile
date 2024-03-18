FROM python:3.10
WORKDIR /backup

ARG VERSION
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir /backup/backup && mkdir /backup/metrics \
    && pip install backup-github-org==${VERSION}
CMD ["backup-github", "--help"]

# Build: docker build . -t backup --build-arg VERSION=1.0.4
# Run: docker run --rm -v .\backup:/backup/backup -v .\metrics:/backup/metrics  backup backup-github --all -t "token" -o "/backup/backup" --metrics_path "/backup/metrics/backup.prom"  "organization"