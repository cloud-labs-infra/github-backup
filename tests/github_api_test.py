import time
import requests
import requests_mock

from backup.main import GithubAPI
import pytest


class TestGithubApi:
    gh = GithubAPI("test_token", "test", ".", 1)

    def test_make_request(self):
        with requests_mock.Mocker() as m:
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer test_token'},
                  response_list=[{'json': [
                      {
                          "login": "octocat",
                          "url": "https://api.github.com/users/octocat",
                          "html_url": "https://github.com/octocat",
                      }
                  ], 'status_code': 200}])
            resp = self.gh.make_request('https://api.github.com/orgs/test/members')
            assert resp == [
                {
                    "login": "octocat",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                }
            ]

    def test_make_request_404(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 404}])
            with pytest.raises(Exception):
                self.gh.make_request('https://api.github.com/orgs/test/members')

    def test_make_request_retry(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 404}, {'json': {}, 'status_code': 200}])
            assert self.gh.make_request('https://api.github.com/orgs/test/members') == {}

    def test_make_request_rate_limit_exceeded_ok(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 403}, {'json': {}, 'status_code': 200}])
            m.get(url='https://api.github.com/rate_limit',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {
                      "resources": {
                          "core": {
                              "limit": 5000,
                              "remaining": 4999,
                              "reset": time.time(),
                              "used": 1
                          },
                      },
                  }, 'status_code': 200}])
            assert self.gh.make_request('https://api.github.com/orgs/test/members') == {}

    def test_make_request_rate_limit_exceeded_fail(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 403}])
            m.get(url='https://api.github.com/rate_limit',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {
                      "resources": {
                          "core": {
                              "limit": 5000,
                              "remaining": 4999,
                              "reset": time.time(),
                              "used": 1
                          },
                      },
                  }, 'status_code': 200}])
            with pytest.raises(Exception):
                assert self.gh.make_request('https://api.github.com/orgs/test/members') == {}

    def test_make_request_timeout(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  exc=requests.exceptions.Timeout)
            with pytest.raises(Exception):
                self.gh.make_request('https://api.github.com/orgs/test/members')
