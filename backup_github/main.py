import logging
import sys
from time import time

from prometheus_client import write_to_textfile

from backup_github.backup import Backup
from backup_github.metrics import (
    backup_duration,
    backup_time,
    git_size,
    meta_size,
    registry,
    success,
)
from backup_github.parse_args import parse_args
from backup_github.utils import count_sizes, upload_to_s3

logging.basicConfig(level=logging.INFO)


def main():
    start = time()
    parsed_args = None
    try:
        parsed_args = parse_args(sys.argv[1:])

        backup = Backup(
            parsed_args.token,
            parsed_args.organization,
            parsed_args.output_dir,
            parsed_args.repository,
        )
        logging.info("Start backup of repos content")
        backup.backup_repositories()
        logging.info("Finish backup of repos content")
        if parsed_args.members or parsed_args.all:
            logging.info("Start backup of members")
            backup.backup_members()
            logging.info("Finish backup of members")
        if parsed_args.issues or parsed_args.all:
            logging.info("Start backup of issues")
            backup.backup_issues()
            logging.info("Finish backup of issues")
        if parsed_args.pulls or parsed_args.all:
            logging.info("Start backup of pulls")
            backup.backup_pulls()
            logging.info("Finish backup of pulls")
        success.labels(parsed_args.organization).set(1)
        if parsed_args.bucket:
            upload_to_s3(
                parsed_args.ak,
                parsed_args.sk,
                parsed_args.output_dir,
                parsed_args.bucket,
                parsed_args.organization,
            )
    except Exception as e:
        logging.error(e)
        success.labels(parsed_args.organization).set(0)
    finally:
        sizes = count_sizes(parsed_args.output_dir)
        git_size.labels(parsed_args.organization).set(sizes["git"])
        meta_size.labels(parsed_args.organization).set(sizes["meta"])
        backup_time.labels(parsed_args.organization).set(int(time()))
        backup_duration.labels(parsed_args.organization).set(time() - start)
        write_to_textfile(f"{parsed_args.metrics_path}", registry)


if __name__ == "__main__":
    main()
