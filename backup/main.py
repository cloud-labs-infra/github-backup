import argparse
import json
import os
import logging
import subprocess
import sys
import time
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
            logging.warning('Output directory does not exist. It will be created')
            os.mkdir(self.output_dir)

    def backup_members(self, api):
        members_dir = self.output_dir + "/members"
        os.makedirs(members_dir, exist_ok=True)
        logging.debug(f'Member dir is {members_dir}')
        org_members = api.get_members()
        logging.debug(f'Got members {org_members}')
        self.__save_members(api, org_members, members_dir)

    def backup_repositories(self, api):
        if self.repositories is None:
            self.repositories = self.__get_repositories(api)
        repo_dir = self.output_dir + "/repositories"
        os.makedirs(repo_dir, exist_ok=True)
        logging.debug(f'Repositories dir is {repo_dir}')
        self.__save_repositories(self.repositories, repo_dir, api)

    def __get_repositories(self, api):
        return [repo['name'] for repo in api.get_repositories()]

    def __save_repositories(self, repositories, dir, api):
        for repository in repositories:
            if os.path.isdir(dir + '/' + repository):
                logging.info(f'Repositories dir {dir}/{repository} exists. Will update repository')
            else:
                logging.info(f'Repositories dir {dir}/{repository} does not exist. Will clone repository')
                repo_content_path = f'{dir}/{repository}/repository'
                os.makedirs(repo_content_path, exist_ok=True)
                os.chdir(repo_content_path)
                repo_url = f'https://{self.token}@github.com/{self.organization}/{repository}.git'
                subprocess.check_call(['git', 'clone', '--mirror', repo_url], stdout=subprocess.DEVNULL,
                                      stderr=subprocess.STDOUT)
            subprocess.check_call(['git', 'fetch', '-p'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            self.__save_main_branch(repository, dir, api)

    def __save_main_branch(self, repository, dir, api):
        branch_name = api.get_main_branch(repository)['default_branch']
        branch_name_path = f'{dir}/{repository}/main_branch.txt'
        with open(branch_name_path, "w+") as f:
            f.write(branch_name)

    def __save_members(self, api, members, dir):
        for member in members:
            status = api.get_member_status(member['login'])
            logging.debug(f'Got status for {member["login"]}: {status}')
            backup_member = {
                "login": member["login"],
                "url": member["url"],
                "html_url": member["html_url"],
                "role": status["role"],
                "state": status["state"]
            }
            with open(f"{dir}/{member['login']}.json", "w+") as member_file:
                logging.debug(f'Save to {dir}/{member["login"]}.json member: {backup_member}')
                json.dump(backup_member, member_file, indent=4)


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
                    logging.warning("Rate limit exceeded")
                    limit = self.get_rate_limit()
                    reset = limit["reset"]
                    seconds = reset - time.time() + self.retry_seconds
                    logging.warning(f"Reset is in {seconds} seconds.")
                    if seconds > 0:
                        logging.info(f"Waiting for {seconds} seconds...")
                        time.sleep(seconds)
                        logging.info("Done waiting - resume!")
                except self.ClientError as e:
                    logging.warning(f"Client error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
                except self.ServerError as e:
                    logging.warning(f"Server error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
                except requests.exceptions.Timeout as e:
                    logging.warning(f"Timeout error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
                except requests.exceptions.ConnectionError as e:
                    logging.warning(f"Connection error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
            raise Exception(f"Failed for {self.retry_count + 1} times")

        return ret

    def __init__(self, token, organization, output_dir, retry_count=10, retry_seconds=1):
        self.headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token}
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.retry_count = retry_count
        self.retry_seconds = retry_seconds

    @retry
    def make_request(self, url):
        resp = requests.get(url, headers=self.headers)
        logging.info(f'Make request to {url}')
        self.raise_by_status(resp.status_code)
        logging.info('OK')
        return resp.json()

    def get_organization(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization)

    def get_members(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/members')

    def get_member_status(self, member_login):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/memberships/' + member_login)

    def get_repositories(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/repos')

    def get_main_branch(self, repo_name):
        return self.make_request('https://api.github.com/repos/' + self.organization + '/' + repo_name)

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
                        default=None,
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
    backup.backup_repositories(gh)
