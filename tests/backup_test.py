import argparse
import json
import os
import tempfile

import requests_mock

import pytest

from github_backup.backup import Backup
from github_backup.parse_args import parse_args


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
            'id': 1,
            'login': 'test1',
        },
        {
            'id': 2,
            'login': 'test2',
        }
    ]

    def check_json(self, expected, path):
        assert os.path.isfile(path)
        actual = json.load(open(path))
        assert expected == actual

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
                      "state": "active",
                      "role": "admin"
                  }, 'status_code': 200}])
            m.get(url='https://api.github.com/orgs/org/memberships/test2',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': {
                      "state": "active",
                      "role": "member"
                  }, 'status_code': 200}])
            self.backup.backup_members()
        self.check_json({'id': 1, 'login': 'test1'}, f'{self.backup.output_dir}/members/test1/member.json')
        self.check_json({'id': 2, 'login': 'test2'}, f'{self.backup.output_dir}/members/test2/member.json')
        self.check_json({"role": "admin", "state": "active"}, f'{self.backup.output_dir}/members/test1/membership.json')
        self.check_json({"role": "member", "state": "active"},
                        f'{self.backup.output_dir}/members/test2/membership.json')

    def test_backup_issues(self):
        os.makedirs(self.backup.output_dir + "/repos/test")
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
                  response_list=[{'json': [], 'status_code': 200}])
            self.backup.backup_issues()
        assert not os.path.exists(self.backup.output_dir + '/repos/test/issues/2')
        assert os.path.exists(self.backup.output_dir + '/repos/test/issues/1/comments')

        self.check_json(
            {"title": "test", "body": "test description", "created_at": "2022-10-18T13:00:57Z", "state": "closed"},
            f'{self.backup.output_dir}/repos/test/issues/1/issue.json')
        self.check_json({'login': 'login'}, f'{self.backup.output_dir}/repos/test/issues/1/user.json')
        self.check_json({'login': 'assignee'}, f'{self.backup.output_dir}/repos/test/issues/1/assignee.json')

    def test_backup_issues_comments(self):
        os.makedirs(self.backup.output_dir + "/repos/test", exist_ok=True)
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
                          'id': 1,
                          'body': 'comment1',
                          'created_at': '2022-10-24T10:05:33Z',
                          'user': {'login': 'login1'},
                      },
                      {
                          'id': 2,
                          'body': 'comment2',
                          'created_at': '2022-10-25T10:05:33Z',
                          'user': {'login': 'login2'},
                      }
                  ], 'status_code': 200}])
            self.backup.backup_issues()
        self.check_json({'id': 1, 'body': 'comment1', 'created_at': '2022-10-24T10:05:33Z'},
                        f'{self.backup.output_dir}/repos/test/issues/1/comments/1/comment.json')
        self.check_json({'login': 'login1'}, f'{self.backup.output_dir}/repos/test/issues/1/comments/1/user.json')
        self.check_json({'id': 2, 'body': 'comment2', 'created_at': '2022-10-25T10:05:33Z'},
                        f'{self.backup.output_dir}/repos/test/issues/1/comments/2/comment.json')
        self.check_json({'login': 'login2'}, f'{self.backup.output_dir}/repos/test/issues/1/comments/2/user.json')

    def test_backup_pull(self):
        os.makedirs(self.backup.output_dir + "/repos/test", exist_ok=True)
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
                          'head': {'ref': 'test-branch', 'sha': '22dhjw4456fkeavkaw9jv'},
                          'base': {'ref': 'master', 'sha': '267ud8ihjw45wdfvas6fk'},
                          'html_url': 'https://github.com/normal-pull',
                          'merge_commit_sha': '267ud8ihjw45wdfvas6fk'
                      },
                      {
                          'number': 2,
                          'title': 'test2',
                          'body': 'test description',
                          'created_at': '2022-10-11T13:00:57Z',
                          'user': {'login': 'login'},
                          'state': 'open',
                          'assignee': {'login': 'assignee'},
                          'head': {'ref': 'test-branch2', 'sha': '22dhjw4we9dfkekaw9jv'},
                          'base': {'ref': 'master', 'sha': '267ud8ihjw45wdfvas6fk'},
                          'html_url': 'https://github.com/issue',
                          'merge_commit_sha': '267ud8ihjwkrvs6fk'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/issues/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [], 'status_code': 200}])
            self.backup.backup_pulls()
        assert not os.path.exists(self.backup.output_dir + '/repos/test/issues/2')
        self.check_json(
            {'title': 'test', 'body': 'test description', 'created_at': '2022-10-18T13:00:57Z', 'state': 'closed', 'merge_commit_sha': '267ud8ihjw45wdfvas6fk'},
            f'{self.backup.output_dir}/repos/test/pulls/1/pull.json')
        self.check_json({'login': 'login'}, f'{self.backup.output_dir}/repos/test/pulls/1/user.json')
        self.check_json({'login': 'assignee'}, f'{self.backup.output_dir}/repos/test/pulls/1/assignee.json')
        self.check_json({'ref': 'test-branch', 'sha': '22dhjw4456fkeavkaw9jv'}, f'{self.backup.output_dir}/repos/test/pulls/1/head.json')
        self.check_json({'ref': 'master', 'sha': '267ud8ihjw45wdfvas6fk'}, f'{self.backup.output_dir}/repos/test/pulls/1/base.json')

    def test_backup_pull_comments(self):
        os.makedirs(self.backup.output_dir + "/repos/test", exist_ok=True)
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
                          'head': {'ref': 'test-branch', 'sha': '22dhjw4456fkeavkaw9jv'},
                          'base': {'ref': 'master', 'sha': '267ud8ihjw45wdfvas6fk'},
                          'html_url': 'https://github.com/normal-pull',
                          'merge_commit_sha': '267ud8ihjw45wdfvas6fk'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/issues/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'id': 1,
                          'body': 'comment1',
                          'created_at': '2022-10-24T10:05:33Z',
                          'user': {'login': 'login1'},
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [], 'status_code': 200}])
            self.backup.backup_pulls()
        self.check_json({'id': 1, 'body': 'comment1', 'created_at': '2022-10-24T10:05:33Z'},
                        f'{self.backup.output_dir}/repos/test/pulls/1/comments/1/comment.json')
        self.check_json({'login': 'login1'}, f'{self.backup.output_dir}/repos/test/pulls/1/comments/1/user.json')

    def test_backup_pull_review(self):
        os.makedirs(self.backup.output_dir + "/repos/test", exist_ok=True)
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
                          'head': {'ref': 'test-branch', 'sha': '22dhjw4456fkeavkaw9jv'},
                          'base': {'ref': 'master', 'sha': '267ud8ihjw45wdfvas6fk'},
                          'html_url': 'https://github.com/normal-pull',
                          'merge_commit_sha': '267ud8ihjw45wdfvas6fk'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/issues/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'id': 1,
                          'body': 'comment1',
                          'created_at': '2022-10-24T10:05:33Z',
                          'user': {'login': 'login1'},
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
                          'commit_id': 2,
                          'user': {'login': 'login1'},
                          'state': 'active'
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews/1/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [
                      {
                          'id': 1,
                          'body': 'comment1',
                          'created_at': '2022-10-25T10:05:33Z',
                          'user': {'login': 'login2'},
                          'diff_hunk': 'some diff1',
                          'path': 'file.txt',
                          'position': 1,
                          'original_position': 1,
                          'commit_id': 1,
                          'original_commit_id': 1,
                          'in_reply_to_id': 24621741
                      }
                  ], 'status_code': 200}])
            m.get(url='https://api.github.com/repos/org/test/pulls/1/reviews/2/comments',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer token'},
                  response_list=[{'json': [], 'status_code': 200}])
            self.backup.backup_pulls()
        self.check_json({'id': 1, 'body': 'comment_review1', 'state': 'active', 'submitted_at': '2022-10-24T10:05:33Z',
                         'commit_id': 2},
                        f'{self.backup.output_dir}/repos/test/pulls/1/reviews/1/review.json')
        self.check_json({'login': 'login1'}, f'{self.backup.output_dir}/repos/test/pulls/1/reviews/1/user.json')
        self.check_json({'id': 1, 'body': 'comment1', 'created_at': '2022-10-25T10:05:33Z', 'diff_hunk': 'some diff1',
                         'path': 'file.txt', 'position': 1, 'original_position': 1, 'commit_id': 1,
                         'original_commit_id': 1, 'in_reply_to_id': 24621741},
                        f'{self.backup.output_dir}/repos/test/pulls/1/reviews/1/comments/1/comment.json')
        self.check_json({'login': 'login2'},
                        f'{self.backup.output_dir}/repos/test/pulls/1/reviews/1/comments/1/user.json')
