import argparse


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


def parse_args(args=None) -> argparse.Namespace:
    parser = Parser(
        prog="./venv/bin/python github_backup/main.py",
        description="Backup a GitHub organization",
    )
    parser.add_argument(
        "organization",
        metavar="ORGANIZATION_NAME",
        type=str,
        help="github organization name",
    )
    parser.add_argument(
        "-t", "--token", type=str, default="", dest="token", help="personal token"
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        type=str,
        default=".",
        dest="output_dir",
        help="directory for backup",
    )
    parser.add_argument(
        "-r",
        "--repository",
        nargs="+",
        default=None,
        dest="repository",
        help="name of repositories to limit backup",
    )
    parser.add_argument(
        "-i",
        "--issues",
        action="store_true",
        dest="issues",
        help="run backup of issues",
    )
    parser.add_argument(
        "-p",
        "--pulls",
        action="store_true",
        dest="pulls",
        help="run backup of pulls",
    )
    parser.add_argument(
        "-m",
        "--members",
        action="store_true",
        dest="members",
        help="run backup of members",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all",
        help="run backup of all data",
    )
    parser.add_argument(
        "--metrics_path",
        default="/var/lib/node_exporter",
        dest="metrics_path",
        help="path for .prom file with metrics",
    )
    parsed = parser.parse_args(args)
    return parsed
