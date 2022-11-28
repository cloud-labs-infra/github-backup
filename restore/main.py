import argparse
import glob
import json
import os
import logging
import subprocess
import sys
import time

import requests


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


class Restore:
    token = str
    output_dir = str
    organization = str

    def __init__(self, token, backup_dir, organization):
        self.token = token
        self.organization = organization
        self.backup_dir = backup_dir
        if not os.path.isdir(self.backup_dir):
            logging.warning('Output directory does not exist')
            os.mkdir(self.backup_dir)

    def restore_members(self, api):
        members_dir = self.backup_dir + '/members'
        members_files = glob.glob(f'{members_dir}/*.json')
        for member_file in members_files:
            member = json.load(open(member_file))
            if member['state'] != 'active':
                continue
            membership = json.load(open(f'{self.backup_dir}/memberships/{member["login"]}.json'))['role']
            api.invite_member(member['id'], membership)

    def restore_repositories(self, api):
        repos_dir = self.backup_dir + '/repos/'
        repos = os.listdir(repos_dir)
        for repo in repos:
            private = json.load(open(f'{repos_dir}/{repo}/repo.json'))['private']
            api.create_repository(repo, private)

            repo_content = repos_dir + repo + '/content'
            os.chdir(repo_content)
            repo_url = f'https://{self.token}@github.com/{self.organization}/{repo}.git'
            subprocess.check_call(['git', 'push', '--mirror', repo_url], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.STDOUT)


class GithubAPI:
    headers = dict
    token = str
    output_dir = str
    organization = str
    retry_count = int
    retry_seconds = int

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
            logging.info('Status is 403 - Rate limit exceeded exception')
            raise self.RateLimitExceededException()
        elif status == 404:
            logging.info(f'Status is {status} - Client error: Not found')
            raise self.ClientError()
        elif 400 <= status < 500:
            logging.info(f'Status is {status} - Client error')
            raise self.ClientError()
        elif 500 <= status < 600:
            logging.info(f'Status is {status} - Server error')
            raise self.ServerError()

    def retry(func):
        def ret(self, *args, **kwargs):
            for _ in range(self.retry_count + 1):
                try:
                    return func(self, *args, **kwargs)
                except self.RateLimitExceededException:
                    logging.warning('Rate limit exceeded')
                    limit = self.get_rate_limit()
                    reset = limit['reset']
                    seconds = reset - time.time() + self.retry_seconds
                    logging.warning(f'Reset is in {seconds} seconds.')
                    if seconds > 0:
                        logging.info(f'Waiting for {seconds} seconds...')
                        time.sleep(seconds)
                        logging.info('Done waiting - resume!')
                except self.ClientError as e:
                    logging.warning(f'Client error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
                except self.ServerError as e:
                    logging.warning(f'Server error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
                except requests.exceptions.Timeout as e:
                    logging.warning(f'Timeout error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
                except requests.exceptions.ConnectionError as e:
                    logging.warning(f'Connection error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
            raise Exception(f'Failed for {self.retry_count + 1} times')

        return ret

    def __init__(self, token, organization, output_dir, retry_count=10, retry_seconds=1):
        self.headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token}
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.retry_count = retry_count
        self.retry_seconds = retry_seconds

    @retry
    def make_request_post(self, url, body):
        resp = requests.post(url, headers=self.headers, json=body)
        logging.info(f'Make request to {url}')
        self.raise_by_status(resp.status_code)
        logging.info('OK')
        return resp.json()

    def invite_member(self, id, role):
        return self.make_request_post('https://api.github.com/orgs/' + self.organization + '/invitations',
                                      {"invitee_id": id, "role": role})

    def create_repository(self, repo_name, private):
        return self.make_request_post('https://api.github.com/orgs/' + self.organization + '/repos',
                                      {"name": repo_name, "description": "",
                                       "homepage": "https://github.com", "private": private})


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


if __name__ == '__main__':
    parsed_args = None
    backup = None
    try:
        parsed_args = parse_args(sys.argv[1:])
        restore = Restore(parsed_args.token, parsed_args.backup_dir, parsed_args.organization)
        gh = GithubAPI(restore.token, restore.organization, restore.backup_dir)
        restore.restore_repositories(gh)
    except argparse.ArgumentError as e:
        logging.error(e.message)
    except AttributeError as e:
        logging.error(e)
