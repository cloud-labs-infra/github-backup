import glob
import json
import logging
import os
import subprocess

from github_restore.github import GithubAPI


class Restore:
    token = str
    output_dir = str
    organization = str

    def __init__(self, token, backup_dir, organization):
        self.token = token
        self.organization = organization
        self.backup_dir = backup_dir
        if not os.path.isdir(self.backup_dir):
            logging.warning('Output directory does not exist')
            os.mkdir(self.backup_dir)
        self.api = GithubAPI(token, organization, backup_dir)

    def restore_members(self):
        members_dir = self.backup_dir + '/members'
        members_files = glob.glob(f'{members_dir}/*')
        for member_file in members_files:
            member = json.load(open(member_file + "/member.json"))
            membership = json.load(open(member_file + "/membership.json"))
            if membership['state'] != 'active':
                continue
            self.api.invite_member(member['id'], membership['role'])

    def restore_repositories(self):
        repos_dir = self.backup_dir + '/repos/'
        repos = os.listdir(repos_dir)
        for repo in repos:
            private = json.load(open(f'{repos_dir}/{repo}/repo.json'))['private']
            self.api.create_repository(repo, private)

            repo_content = repos_dir + repo + '/content'
            os.chdir(repo_content)
            repo_url = f'https://{self.token}@github.com/{self.organization}/{repo}.git'
            subprocess.check_call(['git', 'push', '--mirror', repo_url], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.STDOUT)

    def restore_issues(self):
        repos_dir = self.backup_dir + '/repos/'
        repos = os.listdir(repos_dir)
        for repo in repos:
            issues_dir = repos_dir + repo + '/issues/'
            issues = os.listdir(issues_dir)
            for issue in issues:
                issue_dir = issues_dir + issue
                issue_json = json.load(open(f'{issues_dir}/{issue}/issue.json'))
                # TODO: can be list of assignee
                assignee = json.load(open(f'{issues_dir}/{issue}/assignee.json'))
                user = json.load(open(f'{issues_dir}/{issue}/user.json'))
                new_issue = self.api.create_issue(repo, issue_json, assignee, user)
                for comment in os.listdir(issue_dir + '/comments'):
                    comment_json = json.load(open(f'{issue_dir}/comments/{comment}/comment.json'))
                    user = json.load(open(f'{issue_dir}/comments/{comment}/user.json'))
                    self.api.create_issue_comment(repo, new_issue, comment_json, user)




