import argparse


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


def parse_args(args=None) -> argparse.Namespace:
    parser = Parser(description='Backup a GitHub organization')
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
    parser.add_argument('-b',
                        '--backup-directory',
                        type=str,
                        default='.',
                        dest='backup_dir',
                        help='backup directory')
    parsed = parser.parse_args(args)
    return parsed
