import argparse
import json
import os
import tempfile

import requests_mock

from backup.main import parse_args, Backup, GithubAPI
import pytest


class TestArgs:
    def test_organization(self):
        args_parsed = parse_args(['test_organization'])
        assert args_parsed.organization == 'test_organization'

    def test_empty_organization(self):
        with pytest.raises(argparse.ArgumentError):
            parse_args(['-t', 'token'])

    def test_token(self):
        args_parsed = parse_args(['-t', 'token', 'test_organization'])
        assert args_parsed.organization == 'test_organization'
        assert args_parsed.token == 'token'

    def test_output_dir(self):
        args_parsed = parse_args(['-t', 'token', '-o', 'test_dir', 'test_organization'])
        assert args_parsed.output_dir == 'test_dir'

    def test_default_output_dir(self):
        args_parsed = parse_args(['-t', 'token', 'test_organization'])
        assert args_parsed.output_dir == '.'


class TestBackup:
    temp_dir = tempfile.TemporaryDirectory()
    backup = Backup('token', 'org', temp_dir.name, None)
    gh = GithubAPI("token", "org", temp_dir.name)
    users = [
        {
            "login": "test1",
            "url": "https://api.github.com/users/test1",
            "html_url": "https://github.com/test1",
        },
        {
            "login": "test2",
            "url": "https://api.github.com/users/test2",
            "html_url": "https://github.com/test2",
        }
    ]

    def test_backup_members(self):
        with requests_mock.Mocker() as m:
            m.get(url='https://api.github.com/orgs/org/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': self.users, 'status_code': 200}])
            m.get(url='https://api.github.com/orgs/org/memberships/test1',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': {
                      "url": "https://api.github.com/orgs/org/memberships/test1",
                      "state": "active",
                      "role": "admin"
                  }, 'status_code': 200}])
            m.get(url='https://api.github.com/orgs/org/memberships/test2',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': {
                      "url": "https://api.github.com/orgs/org/memberships/test1",
                      "state": "active",
                      "role": "member"
                  }, 'status_code': 200}])
            self.backup.backup_members(self.gh)
        assert os.path.isfile(self.backup.output_dir + "/members/" + "test1.json")
        assert os.path.isfile(self.backup.output_dir + "/members/" + "test2.json")
        test1_expected = {
            "login": "test1",
            "url": "https://api.github.com/users/test1",
            "html_url": "https://github.com/test1",
            "role": "admin",
            "state": "active"
        }
        test2_expected = {
            "login": "test2",
            "url": "https://api.github.com/users/test2",
            "html_url": "https://github.com/test2",
            "role": "member",
            "state": "active"
        }
        test1 = json.load(open(self.backup.output_dir + "/members/" + "test1.json"))
        test2 = json.load(open(self.backup.output_dir + "/members/" + "test2.json"))
        assert test1 == test1_expected
        assert test2 == test2_expected
