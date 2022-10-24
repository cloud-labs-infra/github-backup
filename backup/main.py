import argparse
import json
import os
import logging
import sys
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

    def __init__(self, token, organization, output_dir):
        self.headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token}
        self.token = token
        self.organization = organization
        self.output_dir = output_dir

    def get_organization(self):
        resp = requests.get('https://api.github.com/orgs/' + self.organization, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_members(self):
        resp = requests.get('https://api.github.com/orgs/' + self.organization + '/members',
                            headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_member_status(self, member_login):
        resp = requests.get('https://api.github.com/orgs/' + self.organization + '/memberships/' + member_login,
                            headers=self.headers)
        resp.raise_for_status()
        return resp.json()


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
