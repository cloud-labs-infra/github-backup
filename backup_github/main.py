import argparse
import logging
import os
import sys
from time import time

from prometheus_client import write_to_textfile

from backup_github.backup import Backup
from backup_github.metrics import backup_time, git_size, meta_size, registry, success
from backup_github.parse_args import parse_args

logging.basicConfig(level=logging.INFO)


def main():
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
        success.set(1)
    except argparse.ArgumentError as e:
        logging.error(e.message)
        success.set(0)
    except AttributeError as e:
        logging.error(e)
        success.set(0)
    finally:
        backup_time.set(int(time()))
        meta_size.set(
            sum(
                os.path.getsize(f)
                for f in os.listdir(parsed_args.output_dir)
                if os.path.isfile(f)
            )
            - git_size._value.get()
        )
        write_to_textfile(f"{parsed_args.metrics_path}/github_backup.prom", registry)


if __name__ == "__main__":
    main()
