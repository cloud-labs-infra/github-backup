from prometheus_client import CollectorRegistry, Gauge

registry = CollectorRegistry()
success = Gauge(
    "github_backup_success",
    "1 if backup is okay",
    labelnames=["organization"],
    registry=registry,
)
backup_time = Gauge(
    "github_backup_last_timestamp_seconds",
    "time of last backup in unixtime",
    labelnames=["organization"],
    registry=registry,
)
git_size = Gauge(
    "github_backup_git_size_bytes",
    "Total size of git data",
    labelnames=["organization"],
    registry=registry,
)
meta_size = Gauge(
    "github_backup_meta_size_bytes",
    "Total size of meta data",
    labelnames=["organization"],
    registry=registry,
)
backup_duration = Gauge(
    "github_backup_duration_seconds",
    "duration of last backup in seconds",
    labelnames=["organization"],
    registry=registry,
)
rate_limit_count = Gauge(
    "github_backup_rate_limit_count",
    "count of rate limit",
    labelnames=["organization"],
    registry=registry,
)
