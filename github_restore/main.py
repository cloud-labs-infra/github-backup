import argparse
import logging
import sys

from github_restore.parse_args import parse_args
from github_restore.restore import Restore

if __name__ == '__main__':
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args(sys.argv[1:])
        restore = Restore(parsed_args.token, parsed_args.backup_dir, parsed_args.organization)
        #restore.restore_members()
        restore.restore_repositories()
        restore.restore_issues()
    except argparse.ArgumentError as e:
        logging.error(e.message)
    except AttributeError as e:
        logging.error(e)
