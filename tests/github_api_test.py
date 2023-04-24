import time

import pytest
import requests
import requests_mock

from backup_github.github import GithubAPI


class TestGithubApi:
    gh = GithubAPI("test_token", "test", ".", 1, 1)
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer test_token",
    }
    empty_ok = {"json": [], "status_code": 200}
    empty_fail = {"json": {}, "status_code": 404}
    message_fail = {
        "status_code": 404,
        "content": bytes('{"message": "failed"}', "utf-8"),
    }
    rate_limit = {
        "resources": {
            "core": {
                "limit": 5000,
                "remaining": 4999,
                "reset": time.time(),
                "used": 1,
            },
        },
    }

    def test_make_request(self):
        with requests_mock.Mocker() as m:
            m.get(
                url="https://api.github.com/orgs/test/members?page=1",
                request_headers=self.headers,
                response_list=[
                    {
                        "json": [
                            {
                                "login": "octocat",
                                "url": "https://api.github.com/users/octocat",
                                "html_url": "https://github.com/octocat",
                            }
                        ],
                        "status_code": 200,
                    }
                ],
            )
            m.get(
                url="https://api.github.com/orgs/test/members?page=2",
                request_headers=self.headers,
                response_list=[self.empty_ok],
            )
            resp = self.gh.make_request("https://api.github.com/orgs/test/members")
            assert resp == [
                {
                    "login": "octocat",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                }
            ]

    def test_make_request_404(self):
        with requests_mock.Mocker() as m:
            m.get(
                url="https://api.github.com/orgs/test/members",
                request_headers=self.headers,
                response_list=[self.empty_fail],
            )
            with pytest.raises(Exception):
                self.gh.make_request("https://api.github.com/orgs/test/members")

    def test_make_request_retry(self):
        with requests_mock.Mocker() as m:
            m.get(
                url="https://api.github.com/orgs/test/members",
                request_headers=self.headers,
                response_list=[
                    self.message_fail,
                    self.empty_ok,
                ],
            )
            assert (
                self.gh.make_request("https://api.github.com/orgs/test/members") == []
            )

    def test_make_request_rate_limit_exceeded_ok(self):
        with requests_mock.Mocker() as m:
            m.get(
                url="https://api.github.com/orgs/test/members",
                request_headers=self.headers,
                response_list=[
                    self.message_fail,
                    self.empty_ok,
                ],
            )
            m.get(
                url="https://api.github.com/rate_limit",
                request_headers=self.headers,
                response_list=[
                    {
                        "json": self.rate_limit,
                        "status_code": 200,
                    }
                ],
            )
            assert (
                self.gh.make_request("https://api.github.com/orgs/test/members") == []
            )

    def test_make_request_rate_limit_exceeded_fail(self):
        with requests_mock.Mocker() as m:
            m.get(
                url="https://api.github.com/orgs/test/members",
                request_headers=self.headers,
                response_list=[self.message_fail],
            )
            m.get(
                url="https://api.github.com/rate_limit",
                request_headers=self.headers,
                response_list=[
                    {
                        "json": self.rate_limit,
                        "status_code": 200,
                    }
                ],
            )
            with pytest.raises(Exception):
                assert (
                    self.gh.make_request("https://api.github.com/orgs/test/members")
                    == {}
                )

    def test_make_request_timeout(self):
        with requests_mock.Mocker() as m:
            m.get(
                url="https://api.github.com/orgs/test/members",
                request_headers=self.headers,
                exc=requests.exceptions.Timeout,
            )
            with pytest.raises(Exception):
                self.gh.make_request("https://api.github.com/orgs/test/members")
