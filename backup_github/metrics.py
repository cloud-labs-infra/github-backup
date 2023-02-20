from prometheus_client import CollectorRegistry, Gauge

registry = CollectorRegistry()
success = Gauge("github_backup_success", "1 if backup is okay", registry=registry)
time = Gauge(
    "github_backup_last_timestamp_seconds",
    "time of last backup in unixtime",
    registry=registry,
)
git_size = Gauge(
    "github_backup_git_size_bytes", "Total size of git data", registry=registry
)
meta_size = Gauge(
    "github_backup_meta_size_bytes", "Total size of meta data", registry=registry
)
