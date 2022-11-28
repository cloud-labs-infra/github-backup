import argparse
import logging
import sys

from backup.backup import Backup
from backup.github import GithubAPI
from backup.parse_args import parse_args


if __name__ == "__main__":
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args(sys.argv[1:])
        backup = Backup(parsed_args.token, parsed_args.organization, parsed_args.output_dir, parsed_args.repository)
    except argparse.ArgumentError as e:
        logging.error(e.message)
    except AttributeError as e:
        logging.error(e)
    gh = GithubAPI(backup.token, backup.organization, backup.output_dir)
    backup.backup_members(gh)
    backup.backup_repositories(gh)
    backup.backup_issues(gh)
    backup.backup_pulls(gh)
