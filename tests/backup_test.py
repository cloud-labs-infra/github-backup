import argparse
import json
import os
import tempfile

import pytest
import requests_mock

from backup_github.backup import Backup
from backup_github.parse_args import parse_args

os.path.join(os.path.dirname(__file__), "..", "tests/resources")


class TestArgs:
    def test_organization(self):
        args_parsed = parse_args(["test_organization"])
        assert args_parsed.organization == "test_organization"

    def test_empty_organization(self):
        with pytest.raises(argparse.ArgumentError):
            parse_args(["-t", "token"])

    def test_token(self):
        args_parsed = parse_args(["-t", "token", "test_organization"])
        assert args_parsed.organization == "test_organization"
        assert args_parsed.token == "token"

    def test_output_dir(self):
        args_parsed = parse_args(["-t", "token", "-o", "test_dir", "test_organization"])
        assert args_parsed.output_dir == "test_dir"

    def test_default_output_dir(self):
        args_parsed = parse_args(["-t", "token", "test_organization"])
        assert args_parsed.output_dir == "."


class TestBackup:
    temp_dir = tempfile.TemporaryDirectory()
    backup = Backup("token", "org", temp_dir.name, ["test"])
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer token",
    }
    empty_ok = [{"json": [], "status_code": 200}]
    with open("tests/resources/github/users.json") as users_file:
        users = json.load(users_file)
    with open("tests/resources/github/membership.json") as membership_file:
        membership = json.load(membership_file)
    with open("tests/resources/github/issues.json") as issues_file:
        issues = json.load(issues_file)
    with open("tests/resources/github/pulls.json") as pulls_file:
        pulls = json.load(pulls_file)
    with open("tests/resources/github/reviews.json") as reviews_file:
        reviews = json.load(reviews_file)
    with open("tests/resources/github/issues_comments.json") as issues_comments_file:
        issues_comments = json.load(issues_comments_file)
    with open("tests/resources/github/pulls_comments.json") as pulls_comments_file:
        pulls_comments = json.load(pulls_comments_file)
    with open("tests/resources/github/reviews_comments.json") as reviews_comments_file:
        reviews_comments = json.load(reviews_comments_file)

    def mock_github(self, m):
        m.get(
            url="https://api.github.com/orgs/org/members?page=1",
            request_headers=self.headers,
            response_list=[{"json": self.users, "status_code": 200}],
        )
        m.get(
            url="https://api.github.com/orgs/org/members?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/orgs/org/memberships/user1?page=1",
            request_headers=self.headers,
            response_list=[{"json": self.membership[0], "status_code": 200}],
        )
        m.get(
            url="https://api.github.com/orgs/org/memberships/user2?page=1",
            request_headers=self.headers,
            response_list=[{"json": self.membership[1], "status_code": 200}],
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues?page=1",
            request_headers=self.headers,
            response_list=[
                {
                    "json": self.issues + self.pulls,
                    "status_code": 200,
                }
            ],
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues/1/comments?page=1",
            request_headers=self.headers,
            response_list=[
                {
                    "json": self.issues_comments,
                    "status_code": 200,
                }
            ],
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues/1/comments?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues/2/comments?page=1",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls?page=1",
            request_headers=self.headers,
            response_list=[
                {
                    "json": self.issues + self.pulls,
                    "status_code": 200,
                }
            ],
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues/3/comments?page=1",
            request_headers=self.headers,
            response_list=[
                {
                    "json": self.pulls_comments,
                    "status_code": 200,
                }
            ],
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues/3/comments?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/issues/4/comments?page=1",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls/3/reviews?page=1",
            request_headers=self.headers,
            response_list=[
                {
                    "json": self.reviews,
                    "status_code": 200,
                }
            ],
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls/3/reviews?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls/4/reviews?page=1",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls/3/reviews/1/comments?page=1",
            request_headers=self.headers,
            response_list=[
                {
                    "json": self.reviews_comments,
                    "status_code": 200,
                }
            ],
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls/3/reviews/1/comments?page=2",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )
        m.get(
            url="https://api.github.com/repos/org/test/pulls/3/reviews/2/comments",
            request_headers=self.headers,
            response_list=self.empty_ok,
        )

    def compare_json(self, expected_path, actual_path):
        assert os.path.isfile(actual_path)
        assert os.path.isfile(expected_path)
        expected = json.load(open(expected_path))
        actual = json.load(open(actual_path))
        assert expected == actual

    def test_backup_members(self):
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_members()
        self.compare_json(
            "tests/resources/backup/members/user1/member.json",
            f"{self.backup.output_dir}/members/user1/member.json",
        )
        self.compare_json(
            "tests/resources/backup/members/user2/member.json",
            f"{self.backup.output_dir}/members/user2/member.json",
        )

    def test_backup_membership(self):
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_members()
        self.compare_json(
            "tests/resources/backup/members/user1/membership.json",
            f"{self.backup.output_dir}/members/user1/membership.json",
        )
        self.compare_json(
            "tests/resources/backup/members/user2/membership.json",
            f"{self.backup.output_dir}/members/user2/membership.json",
        )

    def test_backup_pull_is_not_issue(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test")
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_issues()
        assert not os.path.exists(f"{self.backup.output_dir}/repos/test/issues/3")
        assert not os.path.exists(f"{self.backup.output_dir}/repos/test/issues/4")

    def test_backup_issues(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_issues()
        assert os.path.exists(f"{self.backup.output_dir}/repos/test/issues/1/comments")
        assert os.path.exists(f"{self.backup.output_dir}/repos/test/issues/2/comments")

        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/issue.json",
            f"{self.backup.output_dir}/repos/test/issues/1/issue.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/user.json",
            f"{self.backup.output_dir}/repos/test/issues/1/user.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/assignee.json",
            f"{self.backup.output_dir}/repos/test/issues/1/assignee.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/2/issue.json",
            f"{self.backup.output_dir}/repos/test/issues/2/issue.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/2/user.json",
            f"{self.backup.output_dir}/repos/test/issues/2/user.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/2/assignee.json",
            f"{self.backup.output_dir}/repos/test/issues/2/assignee.json",
        )

    def test_backup_issues_comments(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_issues()
        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/comments/1/comment.json",
            f"{self.backup.output_dir}/repos/test/issues/1/comments/1/comment.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/comments/1/user.json",
            f"{self.backup.output_dir}/repos/test/issues/1/comments/1/user.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/comments/2/comment.json",
            f"{self.backup.output_dir}/repos/test/issues/1/comments/2/comment.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/issues/1/comments/2/user.json",
            f"{self.backup.output_dir}/repos/test/issues/1/comments/2/user.json",
        )

    def test_backup_pulls(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_pulls()
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/pull.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/pull.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/user.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/user.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/assignee.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/assignee.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/head.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/head.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/base.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/base.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/4/pull.json",
            f"{self.backup.output_dir}/repos/test/pulls/4/pull.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/4/user.json",
            f"{self.backup.output_dir}/repos/test/pulls/4/user.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/4/assignee.json",
            f"{self.backup.output_dir}/repos/test/pulls/4/assignee.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/4/head.json",
            f"{self.backup.output_dir}/repos/test/pulls/4/head.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/4/base.json",
            f"{self.backup.output_dir}/repos/test/pulls/4/base.json",
        )

    def test_backup_pull_comments(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_pulls()
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/comments/3/comment.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/comments/3/comment.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/comments/3/user.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/comments/3/user.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/comments/4/comment.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/comments/4/comment.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/comments/4/user.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/comments/4/user.json",
        )
        assert not os.listdir(f"{self.backup.output_dir}/repos/test/pulls/4/comments")

    def test_backup_review(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_pulls()
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/reviews/1/review.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/reviews/1/review.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/reviews/1/user.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/reviews/1/user.json",
        )
        assert not os.listdir(f"{self.backup.output_dir}/repos/test/pulls/4/reviews")

    def test_backup_review_comments(self):
        os.makedirs(f"{self.backup.output_dir}/repos/test", exist_ok=True)
        with requests_mock.Mocker() as m:
            self.mock_github(m)
            self.backup.backup_pulls()
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/reviews/1/comments/1/comment.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/reviews/1/comments/1/comment.json",
        )
        self.compare_json(
            "tests/resources/backup/repos/test/pulls/3/reviews/1/comments/1/user.json",
            f"{self.backup.output_dir}/repos/test/pulls/3/reviews/1/comments/1/user.json",
        )
