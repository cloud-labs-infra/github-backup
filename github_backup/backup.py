import json
import logging
import os
import subprocess
from typing import Optional

from github_backup.github import GithubAPI


class Backup:
    token = str
    output_dir = str
    organization = str
    repositories = Optional[list]

    def __init__(self, token, organization, output_dir, repositories):
        self.token = token
        self.organization = organization
        self.output_dir = f'{output_dir}/{organization}'
        self.repositories = repositories
        if not os.path.isdir(output_dir):
            logging.warning('Output directory does not exist. It will be created')
            os.mkdir(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.api = GithubAPI(self.token, self.organization, self.output_dir)

    def backup_members(self):
        members_dir = self.output_dir + "/members"
        os.makedirs(members_dir, exist_ok=True)
        logging.debug(f'Member dir is {members_dir}')
        org_members = self.api.get_members()
        logging.debug(f'Got members {org_members}')
        self.__save_members(org_members, members_dir)

    def backup_pulls(self):
        repo_dir = self.output_dir + "/repositories"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            pulls = self.api.get_pulls(repo)
            os.makedirs(repo_dir + '/' + repo + '/pulls', exist_ok=True)
            self.__save_pulls(pulls, repo_dir + '/' + repo + '/pulls', repo)

    def backup_issues(self):
        repo_dir = self.output_dir + "/repos"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            issues_dir = f'{repo_dir}/{repo}/issues'
            logging.debug(f'Issues dir is {issues_dir}')
            issues = self.api.get_issues(repo)
            os.makedirs(issues_dir, exist_ok=True)
            self.__save_issues(issues, issues_dir, repo)

    def backup_repositories(self):
        if self.repositories is None:
            self.repositories = self.__get_repositories()
        repo_dir = self.output_dir + "/repos"
        os.makedirs(repo_dir, exist_ok=True)
        logging.debug(f'Repositories dir is {repo_dir}')
        self.__save_repositories(self.repositories, repo_dir)

    def filter_fields(self, fields, src):
        return {
            field: src[field] if src else {} for field in fields
        }

    def save_json(self, path, content):
        with open(path, "w+") as file:
            logging.debug(
                f'Save to {file}: {content}')
            json.dump(content, file, indent=4)

    def __get_repositories(self):
        return [repo['name'] for repo in self.api.get_repositories()]

    def __save_repositories(self, repositories, dir):
        for repository in repositories:
            self.__save_repo_content(repository, dir)

            repo = self.api.get_repo(repository)
            backup_repo = self.filter_fields(['id', 'name', 'private', 'fork', 'default_branch', 'visibility'], repo)
            self.save_json(f'{dir}/{repository}/repo.json', backup_repo)

    def __save_repo_content(self, repository, dir):
        if os.path.isdir(f'{dir}/{repository}/content'):
            logging.info(f'Repositories dir {dir}/{repository}/content exists. Will update repository')
        else:
            logging.info(f'Repositories dir {dir}/{repository}/content does not exist. Will clone repository')
            repo_content_path = f'{dir}/{repository}/content'
            os.makedirs(repo_content_path, exist_ok=True)
            os.chdir(repo_content_path)
            repo_url = f'https://{self.token}@github.com/{self.organization}/{repository}.git'
            subprocess.check_call(['git', 'clone', '--mirror', repo_url], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.STDOUT)
        subprocess.check_call(['git', 'fetch', '-p'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def __save_members(self, members, member_dir):
        for member in members:
            os.makedirs(f'{member_dir}/{member["login"]}', exist_ok=True)
            backup_member = self.filter_fields(['id', 'login'], member)
            membership = self.api.get_member_status(member['login'])
            backup_membership = self.filter_fields(['state', 'role'], membership)

            self.save_json(f'{member_dir}/{member["login"]}/member.json', backup_member)
            self.save_json(f'{member_dir}/{member["login"]}/membership.json', backup_membership)

    def __save_issues(self, issues, dir, repo):
        for issue in issues:
            if 'pull' in issue['html_url']:
                continue

            os.makedirs(f'{dir}/{issue["number"]}', exist_ok=True)
            os.makedirs(f'{dir}/{issue["number"]}/comments', exist_ok=True)

            backup_issue = self.filter_fields(['title', 'body', 'created_at', 'state'], issue)
            backup_assignee = self.filter_fields(['login'], issue['assignee'])
            backup_user = self.filter_fields(['login'], issue['user'])

            self.save_json(f'{dir}/{issue["number"]}/issue.json', backup_issue)
            self.save_json(f'{dir}/{issue["number"]}/assignee.json', backup_assignee)
            self.save_json(f'{dir}/{issue["number"]}/user.json', backup_user)

            for comment in self.api.get_comments_for_issue(repo, issue['number']):
                os.makedirs(f'{dir}/{issue["number"]}/comments/{comment["id"]}', exist_ok=True)
                backup_comment = self.filter_fields(['id', 'body', 'created_at'], comment)
                backup_user = self.filter_fields(['login'], comment['user'])

                self.save_json(f'{dir}/{issue["number"]}/comments/{comment["id"]}/comment.json', backup_comment)
                self.save_json(f'{dir}/{issue["number"]}/comments/{comment["id"]}/user.json', backup_user)

    def __save_pulls(self, pulls, dir, repo):
        for pull in pulls:
            if 'pull' not in pull['html_url']:
                continue
            comments = [
                {
                    "comment": comment['body'],
                    "creation_date": comment['created_at'],
                    "creator_login": comment['user']['login']
                } for comment in self.api.get_comments_for_issue(repo, pull['number'])
            ]
            review_comments = []
            for review in self.api.get_reviews(repo, pull['number']):
                if len(review['body']):
                    comments.append(
                        {
                            "comment": review['body'],
                            "creation_date": review['submitted_at'],
                            "creator_login": review['user']['login']
                        }
                    )
                review_comments = review_comments + [
                    {
                        "comment": comment['body'],
                        "creation_date": comment['created_at'],
                        "creator_login": comment['user']['login'],
                        "diff": comment['diff_hunk'],
                        "path": comment['path']
                    } for comment in self.api.get_comments_for_pull(repo, pull['number'], review['id'])
                ]
            backup_pull = {
                "title": pull['title'],
                "description": pull['body'],
                "creation_date": pull['created_at'],
                "creator_login": pull['user']['login'],
                "status": pull['state'],
                "assignee_login": pull['assignee']['login'] if pull['assignee'] else None,
                "from_branch": pull['head']['ref'],
                "to_branch": pull['base']['ref'],
                "comments": comments,
                "review_comments": review_comments
            }
            with open(f"{dir}/{pull['number']}.json", "w+") as pull_file:
                logging.debug(f'Save to {dir}/{pull["number"]}.json pull: {backup_pull}')
                json.dump(backup_pull, pull_file, indent=4)
