import argparse
import logging
import sys

from backup_github.backup import Backup
from backup_github.parse_args import parse_args

logging.basicConfig(level=logging.NOTSET)


def main():
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args(sys.argv[1:])
        backup = Backup(
            parsed_args.token,
            parsed_args.organization,
            parsed_args.output_dir,
            parsed_args.repository,
        )
        backup.backup_members()
        backup.backup_repositories()
        backup.backup_issues()
        backup.backup_pulls()
    except argparse.ArgumentError as e:
        logging.error(e.message)
    except AttributeError as e:
        logging.error(e)


if __name__ == "__main__":
    main()
