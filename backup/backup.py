import json
import logging
import os
import subprocess
from typing import Optional

from backup.github import GithubAPI


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
        os.mkdir(self.output_dir)
        self.api = GithubAPI(self.token, self.organization, self.output_dir)

    def backup_members(self):
        members_dir = self.output_dir + "/members"
        os.makedirs(members_dir, exist_ok=True)
        memberships_dir = self.output_dir + "/memberships"
        os.makedirs(memberships_dir, exist_ok=True)
        logging.debug(f'Member dir is {members_dir}')
        logging.debug(f'Memberships dir is {memberships_dir}')
        org_members = self.api.get_members()
        logging.debug(f'Got members {org_members}')
        self.__save_members(org_members, members_dir, memberships_dir)

    def backup_pulls(self):
        repo_dir = self.output_dir + "/repositories"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            pulls = self.api.get_pulls(repo)
            os.makedirs(repo_dir + '/' + repo + '/pulls', exist_ok=True)
            self.__save_pulls(pulls, repo_dir + '/' + repo + '/pulls', repo)

    def backup_issues(self):
        repo_dir = self.output_dir + "/repositories"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            issues = self.api.get_issues(repo)
            os.makedirs(repo_dir + '/' + repo + '/issues', exist_ok=True)
            self.__save_issues(issues, repo_dir + '/' + repo + '/issues', repo)

    def backup_repositories(self):
        if self.repositories is None:
            self.repositories = self.__get_repositories()
        repo_dir = self.output_dir + "/repositories"
        os.makedirs(repo_dir, exist_ok=True)
        logging.debug(f'Repositories dir is {repo_dir}')
        self.__save_repositories(self.repositories, repo_dir)

    def __get_repositories(self):
        return [repo['name'] for repo in self.api.get_repositories()]

    def __save_repositories(self, repositories, dir):
        for repository in repositories:
            if os.path.isdir(dir + '/' + repository):
                logging.info(f'Repositories dir {dir}/{repository} exists. Will update repository')
            else:
                logging.info(f'Repositories dir {dir}/{repository} does not exist. Will clone repository')
                repo_content_path = f'{dir}/{repository}/repository'
                os.makedirs(repo_content_path, exist_ok=True)
                os.chdir(repo_content_path)
                repo_url = f'https://{self.token}@github.com/{self.organization}/{repository}.git'
                subprocess.check_call(['git', 'clone', '--mirror', repo_url], stdout=subprocess.DEVNULL,
                                      stderr=subprocess.STDOUT)
            subprocess.check_call(['git', 'fetch', '-p'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            self.__save_main_branch(repository, dir)

    def __save_main_branch(self, repository, dir):
        branch_name = self.api.get_main_branch(repository)['default_branch']
        branch_name_path = f'{dir}/{repository}/main_branch.txt'
        with open(branch_name_path, "w+") as f:
            f.write(branch_name)

    def __save_members(self, members, member_dir, membership_dir):
        for member in members:
            backup_member = {
                "id": member["id"],
                "login": member["login"],
                "type": member["type"]
            }
            with open(f"{member_dir}/{member['login']}.json", "w+") as member_file:
                logging.debug(f'Save to {dir}/{member["login"]}.json member: {backup_member}')
                json.dump(backup_member, member_file, indent=4)

            membership = self.api.get_member_status(member['login'])
            logging.debug(f'Got membership for {member["login"]}: {membership}')
            backup_membership = {
                "state": membership["state"],
                "role": membership["role"]
            }
            os.makedirs(f'{membership_dir}/{member["login"]}', exist_ok=True)
            with open(f'{membership_dir}/{member["login"]}/membership.json', "w+") as membership_file:
                logging.debug(
                    f'Save to {membership_dir}/{member["login"]}/membership.json membership: {backup_membership}')
                json.dump(backup_membership, membership_file, indent=4)

    def __save_issues(self, issues, dir, repo):
        for issue in issues:
            if 'pull' in issue['html_url']:
                continue
            comments = [
                {"comment": comment['body'],
                 "creation_date": comment['created_at'],
                 "creator_login": comment['user']['login']}
                for comment in self.api.get_comments_for_issue(repo, issue['number'])]
            backup_issue = {
                "title": issue['title'],
                "description": issue['body'],
                "creation_date": issue['created_at'],
                "creator_login": issue['user']['login'],
                "status": issue['state'],
                "assignee_login": issue['assignee']['login'] if issue['assignee'] else None,
                "comments": comments
            }
            with open(f"{dir}/{issue['number']}.json", "w+") as issue_file:
                logging.debug(f'Save to {dir}/{issue["number"]}.json issue: {backup_issue}')
                json.dump(backup_issue, issue_file, indent=4)

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
