import argparse
import json
import os
import logging
import sys
import time
from datetime import timezone, datetime
from typing import Optional

import requests


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


class Backup:
    token = str
    output_dir = str
    organization = str
    repositories = Optional[list]

    def __init__(self, token, organization, output_dir, repositories):
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.repositories = repositories
        if not os.path.isdir(self.output_dir):
            raise AttributeError('Output directory does not exist')

    def backup_members(self, api):
        members_dir = self.output_dir + "/members"
        os.makedirs(members_dir, exist_ok=True)
        org_members = api.get_members()
        self.__save_members(api, org_members, members_dir)

    def __save_members(self, api, members, dir):
        for member in members:
            status = api.get_member_status(member['login'])
            backup_member = {
                "login": member["login"],
                "url": member["url"],
                "html_url": member["html_url"],
                "role": status["role"],
                "state": status["state"]
            }
            with open(f"{dir}/{member['login']}.json", "w+") as member_file:
                json.dump(backup_member, member_file, indent=4)


class GithubAPI:
    headers = dict
    token = str
    output_dir = str
    organization = str
    retry = int

    class RateLimitExceededException(Exception):
        def __init__(self, message=None):
            self.message = message
            super().__init__(self.message)

    class ClientError(Exception):
        def __init__(self, message=None):
            self.message = message
            super().__init__(self.message)

    class ServerError(Exception):
        def __init__(self, message=None):
            self.message = message
            super().__init__(self.message)

    def raise_by_status(self, status):
        if status == 403:
            raise self.RateLimitExceededException()
        if 400 <= status < 500:
            raise self.ClientError()

        elif 500 <= status < 600:
            raise self.ServerError()

    def retry(func):
        def ret(self, *args, **kwargs):
            for _ in range(self.retry + 1):
                try:
                    return func(self, *args, **kwargs)
                except self.RateLimitExceededException:
                    logging.warning(f"Rate limit exceeded")
                    limit = self.get_rate_limit()
                    reset = limit["reset"].replace(tzinfo=timezone.utc)
                    seconds = (reset - datetime.now(timezone.utc)).total_seconds() + 10
                    logging.warning(f"Reset is in {seconds} seconds.")
                    if seconds > 0.0:
                        logging.info(f"Waiting for {seconds} seconds...")
                        time.sleep(seconds)
                        logging.info("Done waiting - resume!")
                except self.ClientError as e:
                    logging.warning(f"Client error: {e}. Try to retry in 5 seconds")
                    time.sleep(5)
                except self.ServerError as e:
                    logging.warning(f"Server error: {e}. Try to retry in 5 seconds")
                    time.sleep(5)
                except requests.exceptions.Timeout as e:
                    logging.warning(f"Timeout error: {e}. Try to retry in 5 seconds")
                    time.sleep(5)
                except requests.exceptions.ConnectionError as e:
                    logging.warning(f"Connection error: {e}. Try to retry in 5 seconds")
                    time.sleep(5)
            raise Exception("Failed too many times")

        return ret

    def __init__(self, token, organization, output_dir, retry=10):
        self.headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token}
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.retry = retry

    @retry
    def make_request(self, url):
        resp = requests.get(url, headers=self.headers)
        self.raise_by_status(resp.status_code)
        return resp.json()

    def get_organization(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization)

    def get_members(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/members')

    def get_member_status(self, member_login):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/memberships/' + member_login)

    def get_rate_limit(self):
        return self.make_request('https://api.github.com/rate_limit')["resources"]["core"]


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
    parser.add_argument('-o',
                        '--output-directory',
                        type=str,
                        default='.',
                        dest='output_dir',
                        help='directory for backup')
    parser.add_argument('-r',
                        '--repository',
                        nargs='+',
                        default='',
                        dest='repository',
                        help='name of repositories to limit backup')
    parsed = parser.parse_args(args)
    return parsed


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
