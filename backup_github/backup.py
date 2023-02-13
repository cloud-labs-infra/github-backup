import json
import logging
import os
import subprocess
import sys
from typing import Optional

from backup_github.github import GithubAPI


def save_json(path, content):
    mode = 'a' if os.path.exists(path) else 'w'
    with open(path, mode) as file:
        logging.debug(f'Save to {file}: {content}')
        json.dump(content, file, indent=4)


def filter_fields(fields, src):
    return {
        field: src[field] if src and field in src else None for field in fields
    }


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
        repo_dir = self.output_dir + "/repos"
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

    def __get_repositories(self):
        return [repo['name'] for repo in self.api.get_repositories()]

    def __save_repositories(self, repositories, dir):
        for repository in repositories:
            self.__save_repo_content(repository, dir)

            repo = self.api.get_repo(repository)
            backup_repo = filter_fields(['id', 'name', 'private', 'fork', 'default_branch', 'visibility'], repo)
            save_json(f'{dir}/{repository}/repo.json', backup_repo)

    def __save_repo_content(self, repository, dir):
        cur_dir = os.getcwd()
        repo_content_path = f'{dir}/{repository}/content'
        if os.path.isdir(repo_content_path):
            logging.info(f'Repositories dir {dir}/{repository}/content exists. Will update repository')
            os.chdir(repo_content_path)
        else:
            logging.info(f'Repositories dir {dir}/{repository}/content does not exist. Will clone repository')
            os.makedirs(repo_content_path, exist_ok=True)
            os.chdir(repo_content_path)
            repo_url = f'https://{self.token}@github.com/{self.organization}/{repository}.git'
            try:
                subprocess.check_output(['git', 'clone', '--bare', repo_url])
            except subprocess.CalledProcessError as e:
                print('exit code: {}'.format(e.returncode))
                print('stdout: {}'.format(e.output.decode(sys.getfilesystemencoding())))
                print('stderr: {}'.format(e.stderr.decode(sys.getfilesystemencoding())))
        os.chdir(f'{repository}.git')
        try:
            subprocess.check_output(['git', 'fetch', '-p'])
        except subprocess.CalledProcessError as e:
            print('exit code: {}'.format(e.returncode))
            print('stdout: {}'.format(e.output.decode(sys.getfilesystemencoding())))
            print('stderr: {}'.format(e.stderr.decode(sys.getfilesystemencoding())))
        os.chdir(cur_dir)

    def __save_members(self, members, member_dir):
        for member in members:
            os.makedirs(f'{member_dir}/{member["login"]}', exist_ok=True)
            backup_member = filter_fields(['id', 'login'], member)
            membership = self.api.get_member_status(member['login'])
            backup_membership = filter_fields(['state', 'role'], membership)

            save_json(f'{member_dir}/{member["login"]}/member.json', backup_member)
            save_json(f'{member_dir}/{member["login"]}/membership.json', backup_membership)

    def __save_issues(self, issues, dir, repo):
        for issue in issues:
            if 'pull' in issue['html_url']:
                continue

            os.makedirs(f'{dir}/{issue["number"]}', exist_ok=True)
            os.makedirs(f'{dir}/{issue["number"]}/comments', exist_ok=True)

            backup_issue = filter_fields(['title', 'body', 'created_at', 'state'], issue)
            backup_assignee = filter_fields(['login'], issue['assignee'])
            backup_user = filter_fields(['login'], issue['user'])

            save_json(f'{dir}/{issue["number"]}/issue.json', backup_issue)
            save_json(f'{dir}/{issue["number"]}/assignee.json', backup_assignee)
            save_json(f'{dir}/{issue["number"]}/user.json', backup_user)

            for comment in self.api.get_comments_for_issue(repo, issue['number']):
                os.makedirs(f'{dir}/{issue["number"]}/comments/{comment["id"]}', exist_ok=True)
                backup_comment = filter_fields(['id', 'body', 'created_at'], comment)
                backup_user = filter_fields(['login'], comment['user'])

                save_json(f'{dir}/{issue["number"]}/comments/{comment["id"]}/comment.json', backup_comment)
                save_json(f'{dir}/{issue["number"]}/comments/{comment["id"]}/user.json', backup_user)

    def __save_pulls(self, pulls, dir, repo):
        for pull in pulls:
            if 'pull' not in pull['html_url']:
                continue

            os.makedirs(f'{dir}/{pull["number"]}', exist_ok=True)
            os.makedirs(f'{dir}/{pull["number"]}/comments', exist_ok=True)
            os.makedirs(f'{dir}/{pull["number"]}/reviews', exist_ok=True)

            backup_pull = filter_fields(['title', 'body', 'created_at', 'state', 'merge_commit_sha'], pull)
            backup_assignee = filter_fields(['login'], pull['assignee'])
            backup_user = filter_fields(['login'], pull['user'])
            backup_head = filter_fields(['ref', 'sha'], pull['head'])
            backup_base = filter_fields(['ref', 'sha'], pull['base'])

            save_json(f'{dir}/{pull["number"]}/pull.json', backup_pull)
            save_json(f'{dir}/{pull["number"]}/assignee.json', backup_assignee)
            save_json(f'{dir}/{pull["number"]}/user.json', backup_user)
            save_json(f'{dir}/{pull["number"]}/head.json', backup_head)
            save_json(f'{dir}/{pull["number"]}/base.json', backup_base)

            for comment in self.api.get_comments_for_issue(repo, pull['number']):
                os.makedirs(f'{dir}/{pull["number"]}/comments/{comment["id"]}', exist_ok=True)
                backup_comment = filter_fields(['id', 'body', 'created_at'], comment)
                backup_user = filter_fields(['login'], comment['user'])

                save_json(f'{dir}/{pull["number"]}/comments/{comment["id"]}/comment.json', backup_comment)
                save_json(f'{dir}/{pull["number"]}/comments/{comment["id"]}/user.json', backup_user)

            for review in self.api.get_reviews(repo, pull['number']):
                os.makedirs(f'{dir}/{pull["number"]}/reviews/{review["id"]}', exist_ok=True)
                backup_review = filter_fields(['id', 'body', 'state', 'submitted_at', 'commit_id'], review)
                backup_user = filter_fields(['login'], review['user'])

                save_json(f'{dir}/{pull["number"]}/reviews/{review["id"]}/review.json', backup_review)
                save_json(f'{dir}/{pull["number"]}/reviews/{review["id"]}/user.json', backup_user)

                for comment in self.api.get_comments_for_review(repo, pull['number'], review['id']):
                    os.makedirs(f'{dir}/{pull["number"]}/reviews/{review["id"]}/comments/{comment["id"]}',
                                exist_ok=True)
                    backup_comment = filter_fields(
                        ['id', 'body', 'created_at', 'diff_hunk', 'path', 'position', 'original_position', 'commit_id',
                         'original_commit_id', 'in_reply_to_id'], comment)
                    backup_user = filter_fields(['login'], comment['user'])

                    save_json(
                        f'{dir}/{pull["number"]}/reviews/{review["id"]}/comments/{comment["id"]}/comment.json',
                        backup_comment)
                    save_json(f'{dir}/{pull["number"]}/reviews/{review["id"]}/comments/{comment["id"]}/user.json',
                              backup_user)

