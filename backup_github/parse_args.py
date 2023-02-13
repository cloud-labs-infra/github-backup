import argparse


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


def parse_args(args=None) -> argparse.Namespace:
    parser = Parser(prog='./venv/bin/python github_backup/main.py', description='Backup a GitHub organization')
    parser.add_argument('organization',
                        metavar='ORGANIZATION_NAME',
                        type=str,
                        help='github organization name')
    parser.add_argument('-t',
                        '--token',
                        type=str,
                        default='',
                        dest='token',
                        help='personal token')
    parser.add_argument('-o',
                        '--output-directory',
                        type=str,
                        default='.',
                        dest='output_dir',
                        help='directory for backup')
    parser.add_argument('-r',
                        '--repository',
                        nargs='+',
                        default=None,
                        dest='repository',
                        help='name of repositories to limit backup')
    parsed = parser.parse_args(args)
    return parsed
