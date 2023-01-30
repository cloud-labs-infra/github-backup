import argparse
import logging
import sys

from github_backup.backup import Backup
from github_backup.parse_args import parse_args

logging.basicConfig(level=logging.NOTSET)

if __name__ == "__main__":
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args(sys.argv[1:])
        backup = Backup(parsed_args.token, parsed_args.organization, parsed_args.output_dir, parsed_args.repository)
        logging.info("Backup of members is started")
        backup.backup_members()
        logging.info("Backup of members is finished")
        logging.info("Backup of repositories is started")
        backup.backup_repositories()
        logging.info("Backup of repositories is finished")
        logging.info("Backup of issues is started")
        backup.backup_issues()
        logging.info("Backup of issues is finished")
        logging.info("Backup of pulls is started")
        backup.backup_pulls()
        logging.info("Backup of pulls is finished")
    except argparse.ArgumentError as e:
        logging.error(e.message)
    except AttributeError as e:
        logging.error(e)
