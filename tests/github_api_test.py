import requests
import requests_mock

from backup.main import GithubAPI
import pytest


class TestGithubApi:
    gh = GithubAPI("test_token", "test", ".")

    def test_get_organization(self):
        with requests_mock.Mocker() as m:
            m.get(url='https://api.github.com/orgs/test',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer test_token'},
                  response_list=[{'json': {
                      "login": "github",
                      "url": "https://api.github.com/orgs/github",
                      "repos_url": "https://api.github.com/orgs/github/repos",
                      "events_url": "https://api.github.com/orgs/github/events",
                      "hooks_url": "https://api.github.com/orgs/github/hooks",
                      "issues_url": "https://api.github.com/orgs/github/issues",
                      "members_url": "https://api.github.com/orgs/github/members{/member}",
                      "public_members_url": "https://api.github.com/orgs/github/public_members{/member}",
                      "description": "A great organization",
                      "name": "github",
                      "company": "GitHub",
                      "blog": "https://github.com/blog",
                      "location": "San Francisco",
                      "email": "octocat@github.com",
                      "twitter_username": "github",
                      "is_verified": "true",
                      "has_organization_projects": "true",
                      "has_repository_projects": "true",
                      "html_url": "https://github.com/octocat",
                      "created_at": "2008-01-14T04:33:35Z",
                      "updated_at": "2014-03-03T18:58:10Z",
                      "total_private_repos": 100,
                      "owned_private_repos": 100,
                      "collaborators": 8,
                      "billing_email": "mona@github.com",
                  }, 'status_code': 200}])
            resp = self.gh.get_organization()
            assert resp == {
                      "login": "github",
                      "url": "https://api.github.com/orgs/github",
                      "repos_url": "https://api.github.com/orgs/github/repos",
                      "events_url": "https://api.github.com/orgs/github/events",
                      "hooks_url": "https://api.github.com/orgs/github/hooks",
                      "issues_url": "https://api.github.com/orgs/github/issues",
                      "members_url": "https://api.github.com/orgs/github/members{/member}",
                      "public_members_url": "https://api.github.com/orgs/github/public_members{/member}",
                      "description": "A great organization",
                      "name": "github",
                      "company": "GitHub",
                      "blog": "https://github.com/blog",
                      "location": "San Francisco",
                      "email": "octocat@github.com",
                      "twitter_username": "github",
                      "is_verified": "true",
                      "has_organization_projects": "true",
                      "has_repository_projects": "true",
                      "html_url": "https://github.com/octocat",
                      "created_at": "2008-01-14T04:33:35Z",
                      "updated_at": "2014-03-03T18:58:10Z",
                      "total_private_repos": 100,
                      "owned_private_repos": 100,
                      "collaborators": 8,
                      "billing_email": "mona@github.com",
                  }

    def test_get_organization_404(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 404}])
            with pytest.raises(requests.exceptions.RequestException):
                self.gh.get_organization()

    def test_get_organization_timeout(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  exc=requests.exceptions.ConnectTimeout)
            with pytest.raises(requests.exceptions.ConnectTimeout):
                self.gh.get_organization()

    def test_get_members(self):
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
            resp = self.gh.get_members()
            assert resp == [
                {
                    "login": "octocat",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                }
            ]

    def test_get_members_404(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 404}])
            with pytest.raises(requests.exceptions.RequestException):
                self.gh.get_members()

    def test_get_members_timeout(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/members',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  exc=requests.exceptions.ConnectTimeout)
            with pytest.raises(requests.exceptions.ConnectTimeout):
                self.gh.get_members()

    def test_get_member_status(self):
        with requests_mock.Mocker() as m:
            m.get(url='https://api.github.com/orgs/test/memberships/octocat',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer test_token'},
                  response_list=[{'json': {
                      "url": "https://api.github.com/orgs/octocat/memberships/defunkt",
                      "state": "active",
                      "role": "admin",
                  }, 'status_code': 200}])
            resp = self.gh.get_member_status('octocat')
            assert resp == {
                "url": "https://api.github.com/orgs/octocat/memberships/defunkt",
                "state": "active",
                "role": "admin",
            }

    def test_get_member_status_404(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/memberships/octocat',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  response_list=[{'json': {}, 'status_code': 404}])
            with pytest.raises(requests.exceptions.RequestException):
                self.gh.get_member_status('octocat')

    def test_get_member_status_timeout(self):
        with requests_mock.Mocker() as m:
            token = 'test_token'
            m.get(url='https://api.github.com/orgs/test/memberships/octocat',
                  request_headers={'Accept': 'application/vnd.github+json',
                                   'Authorization': 'Bearer ' + token},
                  exc=requests.exceptions.ConnectTimeout)
            with pytest.raises(requests.exceptions.ConnectTimeout):
                self.gh.get_member_status('octocat')
