import argparse
import os
from typing import Optional


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


class Backup:
    token = str
    output_dir = str
    organization = str
    repositories = Optional[list]

    def __init__(self, token, output_dir, organization, repositories):
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.repositories = repositories
        if not os.path.isdir(self.output_dir):
            raise AttributeError('Output directory does not exist')


def parse_args(args=None) -> argparse.Namespace:
    parser = Parser(description='Backup a GitHub organization')
    parser.add_argument('organization',
                        metavar='ORGANIZATION_NAME',
                        type=str,
                        help='github organization name')
    parser.add_argument('-t',
                        '--token',
                        type=str,
                        dest='token',
                        help='personal access, OAuth, or JSON Web token, or path to token (file://...)')
    parser.add_argument('-o',
                        '--output-directory',
                        default='.',
                        type=str,
                        dest='output_dir',
                        help='directory at which to backup the repositories')
    parser.add_argument('-r',
                        '--repository',
                        nargs='+',
                        dest='repository',
                        help='name of repository to limit backup')
    parsed = parser.parse_args(args)
    return parsed


if __name__ == "__main__":
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args()
        backup = Backup(parsed_args.token, parsed_args.output_dir, parsed_args.organization, parsed_args.repositories)
    except argparse.ArgumentError as e:
        print(e.message)
    except AttributeError as e:
        print(e)
