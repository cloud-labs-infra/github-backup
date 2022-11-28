import argparse
import json
import os
import tempfile

import requests_mock

from backup.main import parse_args, Backup
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
            self.backup.backup_members()
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

    def test_backup_issues(self):
        os.makedirs(self.backup.output_dir + "/repositories/test")
        with requests_mock.Mocker() as m:
            m.get(url='https://api.github.com/repos/org/test/issues',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'number': 1,
                          'title': 'test',
                          'body': 'test description',
                          'created_at': '2022-10-18T13:00:57Z',
                          'user': {'login': 'login'},
                          'state': 'closed',
                          'assignee': {'login': 'assignee'},
                          'html_url': 'https://github.com/normal-issue'
                      },
                      {
                          'number': 2,
                          'title': 'test2',
                          'body': 'test description',
                          'created_at': '2022-10-11T13:00:57Z',
                          'user': {'login': 'login'},
                          'state': 'open',
                          'assignee': {'login': 'assignee'},
                          'html_url': 'https://github.com/pull'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/issues/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'body': 'comment1',
                          'created_at': '2022-10-24T10:05:33Z',
                          'user': {'login': 'login1'},
                      },
                      {
                          'body': 'comment2',
                          'created_at': '2022-10-25T10:05:33Z',
                          'user': {'login': 'login2'},
                      }
                  ], 'status_code': 200}])
            self.backup.backup_issues()
        expected = {
            "title": "test",
            "description": "test description",
            "creation_date": "2022-10-18T13:00:57Z",
            "creator_login": "login",
            "status": "closed",
            "assignee_login": "assignee",
            "comments": [
                {
                    "comment": "comment1",
                    "creation_date": "2022-10-24T10:05:33Z",
                    "creator_login": "login1"
                },
                {
                    "comment": "comment2",
                    "creation_date": "2022-10-25T10:05:33Z",
                    "creator_login": "login2"
                }
            ]
        }
        assert os.path.isfile(self.backup.output_dir + "/repositories/test/issues/" + "1.json")
        assert not os.path.isfile(self.backup.output_dir + "/repositories/test/issues/" + "2.json")
        actual = json.load(open(self.backup.output_dir + "/repositories/test/issues/" + "1.json"))
        assert actual == expected

    def test_backup_pull(self):
        os.makedirs(self.backup.output_dir + "/repositories/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            m.get(url='https://api.github.com/repos/org/test/pulls',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'number': 1,
                          'title': 'test',
                          'body': 'test description',
                          'created_at': '2022-10-18T13:00:57Z',
                          'user': {'login': 'login'},
                          'state': 'closed',
                          'assignee': {'login': 'assignee'},
                          'head': {'ref': 'test-branch'},
                          'base': {'ref': 'master'},
                          'html_url': 'https://github.com/normal-pull'
                      },
                      {
                          'number': 2,
                          'title': 'test2',
                          'body': 'test description',
                          'created_at': '2022-10-11T13:00:57Z',
                          'user': {'login': 'login'},
                          'state': 'open',
                          'assignee': {'login': 'assignee'},
                          'head': {'ref': 'test-branch2'},
                          'base': {'ref': 'master'},
                          'html_url': 'https://github.com/issue'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/issues/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'body': 'comment1',
                          'created_at': '2022-10-24T10:05:33Z',
                          'user': {'login': 'login1'},
                      },
                      {
                          'body': 'comment2',
                          'created_at': '2022-10-25T10:05:33Z',
                          'user': {'login': 'login2'},
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'id': 1,
                          'body': 'comment_review1',
                          'submitted_at': '2022-10-24T10:05:33Z',
                          'user': {'login': 'login1'},
                      },
                      {
                          'id': 2,
                          'body': 'comment_review2',
                          'submitted_at': '2022-10-25T10:05:33Z',
                          'user': {'login': 'login2'},
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'body': 'comment1',
                          'created_at': '2022-10-25T10:05:33Z',
                          'user': {'login': 'login2'},
                          'diff_hunk': 'some diff1',
                          'path': 'file.txt'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews/2/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [], 'status_code': 200}])
            self.backup.backup_pulls()
        expected = {
            "title": "test",
            "description": "test description",
            "creation_date": "2022-10-18T13:00:57Z",
            "creator_login": "login",
            "status": "closed",
            "assignee_login": "assignee",
            "from_branch": "test-branch",
            "to_branch": "master",
            "comments": [
                {
                    "comment": "comment1",
                    "creation_date": "2022-10-24T10:05:33Z",
                    "creator_login": "login1"
                },
                {
                    "comment": "comment2",
                    "creation_date": "2022-10-25T10:05:33Z",
                    "creator_login": "login2"
                },
                {
                    "comment": "comment_review1",
                    "creation_date": "2022-10-24T10:05:33Z",
                    "creator_login": "login1"
                },
                {
                    "comment": "comment_review2",
                    "creation_date": "2022-10-25T10:05:33Z",
                    "creator_login": "login2"
                }
            ],
            "review_comments": [
                {
                    'comment': 'comment1',
                    'creation_date': '2022-10-25T10:05:33Z',
                    'creator_login': 'login2',
                    'diff': 'some diff1',
                    'path': 'file.txt'
                }
            ]
        }
        assert os.path.isfile(self.backup.output_dir + "/repositories/test/pulls/" + "1.json")
        assert not os.path.isfile(self.backup.output_dir + "/repositories/test/pulls/" + "2.json")
        actual = json.load(open(self.backup.output_dir + "/repositories/test/pulls/" + "1.json"))
        assert actual == expected
