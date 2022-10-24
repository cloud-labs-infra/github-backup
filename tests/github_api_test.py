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
                      "id": 1,
                      "node_id": "MDEyOk9yZ2FuaXphdGlvbjE=",
                      "url": "https://api.github.com/orgs/github",
                      "repos_url": "https://api.github.com/orgs/github/repos",
                      "events_url": "https://api.github.com/orgs/github/events",
                      "hooks_url": "https://api.github.com/orgs/github/hooks",
                      "issues_url": "https://api.github.com/orgs/github/issues",
                      "members_url": "https://api.github.com/orgs/github/members{/member}",
                      "public_members_url": "https://api.github.com/orgs/github/public_members{/member}",
                      "avatar_url": "https://github.com/images/error/octocat_happy.gif",
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
                      "public_repos": 2,
                      "public_gists": 1,
                      "followers": 20,
                      "following": 0,
                      "html_url": "https://github.com/octocat",
                      "created_at": "2008-01-14T04:33:35Z",
                      "updated_at": "2014-03-03T18:58:10Z",
                      "type": "Organization",
                      "total_private_repos": 100,
                      "owned_private_repos": 100,
                      "collaborators": 8,
                      "billing_email": "mona@github.com",
                  }, 'status_code': 200}])
            resp = self.gh.get_organization()
            assert resp == {
                "login": "github",
                "id": 1,
                "node_id": "MDEyOk9yZ2FuaXphdGlvbjE=",
                "url": "https://api.github.com/orgs/github",
                "repos_url": "https://api.github.com/orgs/github/repos",
                "events_url": "https://api.github.com/orgs/github/events",
                "hooks_url": "https://api.github.com/orgs/github/hooks",
                "issues_url": "https://api.github.com/orgs/github/issues",
                "members_url": "https://api.github.com/orgs/github/members{/member}",
                "public_members_url": "https://api.github.com/orgs/github/public_members{/member}",
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
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
                "public_repos": 2,
                "public_gists": 1,
                "followers": 20,
                "following": 0,
                "html_url": "https://github.com/octocat",
                "created_at": "2008-01-14T04:33:35Z",
                "updated_at": "2014-03-03T18:58:10Z",
                "type": "Organization",
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
                          "id": 1,
                          "node_id": "MDQ6VXNlcjE=",
                          "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                          "gravatar_id": "",
                          "url": "https://api.github.com/users/octocat",
                          "html_url": "https://github.com/octocat",
                          "followers_url": "https://api.github.com/users/octocat/followers",
                          "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                          "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                          "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                          "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                          "organizations_url": "https://api.github.com/users/octocat/orgs",
                          "repos_url": "https://api.github.com/users/octocat/repos",
                          "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                          "received_events_url": "https://api.github.com/users/octocat/received_events",
                          "type": "User",
                          "site_admin": "false"
                      }
                  ], 'status_code': 200}])
            resp = self.gh.get_members()
            assert resp == [
                {
                    "login": "octocat",
                    "id": 1,
                    "node_id": "MDQ6VXNlcjE=",
                    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                    "followers_url": "https://api.github.com/users/octocat/followers",
                    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/octocat/orgs",
                    "repos_url": "https://api.github.com/users/octocat/repos",
                    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/octocat/received_events",
                    "type": "User",
                    "site_admin": "false"
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
                      "organization_url": "https://api.github.com/orgs/octocat",
                      "organization": {
                          "login": "github",
                          "id": 1,
                          "node_id": "MDEyOk9yZ2FuaXphdGlvbjE=",
                          "url": "https://api.github.com/orgs/github",
                          "repos_url": "https://api.github.com/orgs/github/repos",
                          "events_url": "https://api.github.com/orgs/github/events",
                          "hooks_url": "https://api.github.com/orgs/github/hooks",
                          "issues_url": "https://api.github.com/orgs/github/issues",
                          "members_url": "https://api.github.com/orgs/github/members{/member}",
                          "public_members_url": "https://api.github.com/orgs/github/public_members{/member}",
                          "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                          "description": "A great organization"
                      },
                      "user": {
                          "login": "octocat",
                          "id": 1,
                          "node_id": "MDQ6VXNlcjE=",
                          "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                          "gravatar_id": "",
                          "url": "https://api.github.com/users/octocat",
                          "html_url": "https://github.com/octocat",
                          "followers_url": "https://api.github.com/users/octocat/followers",
                          "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                          "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                          "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                          "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                          "organizations_url": "https://api.github.com/users/octocat/orgs",
                          "repos_url": "https://api.github.com/users/octocat/repos",
                          "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                          "received_events_url": "https://api.github.com/users/octocat/received_events",
                          "type": "User",
                          "site_admin": "false"
                      }
                  }, 'status_code': 200}])
            resp = self.gh.get_member_status('octocat')
            assert resp == {
                "url": "https://api.github.com/orgs/octocat/memberships/defunkt",
                "state": "active",
                "role": "admin",
                "organization_url": "https://api.github.com/orgs/octocat",
                "organization": {
                    "login": "github",
                    "id": 1,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjE=",
                    "url": "https://api.github.com/orgs/github",
                    "repos_url": "https://api.github.com/orgs/github/repos",
                    "events_url": "https://api.github.com/orgs/github/events",
                    "hooks_url": "https://api.github.com/orgs/github/hooks",
                    "issues_url": "https://api.github.com/orgs/github/issues",
                    "members_url": "https://api.github.com/orgs/github/members{/member}",
                    "public_members_url": "https://api.github.com/orgs/github/public_members{/member}",
                    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                    "description": "A great organization"
                },
                "user": {
                    "login": "octocat",
                    "id": 1,
                    "node_id": "MDQ6VXNlcjE=",
                    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                    "followers_url": "https://api.github.com/users/octocat/followers",
                    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/octocat/orgs",
                    "repos_url": "https://api.github.com/users/octocat/repos",
                    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/octocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                }
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
