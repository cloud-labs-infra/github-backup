import argparse
import logging
import sys

from github_backup.backup import Backup
from github_backup.parse_args import parse_args

if __name__ == "__main__":
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args(sys.argv[1:])
        backup = Backup(parsed_args.token, parsed_args.organization, parsed_args.output_dir, parsed_args.repository)
        backup.backup_members()
        backup.backup_repositories()
        backup.backup_issues()
        # backup.backup_pulls()
    except argparse.ArgumentError as e:
        logging.error(e.message)
    except AttributeError as e:
        logging.error(e)
