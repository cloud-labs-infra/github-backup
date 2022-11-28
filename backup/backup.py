import json
import logging
import os
import subprocess
from typing import Optional


class Backup:
    token = str
    output_dir = str
    organization = str
    repositories = Optional[list]

    def __init__(self, token, organization, output_dir, repositories):
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.repositories = repositories
        if not os.path.isdir(self.output_dir):
            logging.warning('Output directory does not exist. It will be created')
            os.mkdir(self.output_dir)

    def backup_members(self, api):
        members_dir = self.output_dir + "/members"
        os.makedirs(members_dir, exist_ok=True)
        logging.debug(f'Member dir is {members_dir}')
        org_members = api.get_members()
        logging.debug(f'Got members {org_members}')
        self.__save_members(api, org_members, members_dir)

    def backup_pulls(self, api):
        repo_dir = self.output_dir + "/repositories"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            pulls = api.get_pulls(repo)
            os.makedirs(repo_dir + '/' + repo + '/pulls', exist_ok=True)
            self.__save_pulls(api, pulls, repo_dir + '/' + repo + '/pulls', repo)

    def backup_issues(self, api):
        repo_dir = self.output_dir + "/repositories"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            issues = api.get_issues(repo)
            os.makedirs(repo_dir + '/' + repo + '/issues', exist_ok=True)
            self.__save_issues(api, issues, repo_dir + '/' + repo + '/issues', repo)

    def backup_repositories(self, api):
        if self.repositories is None:
            self.repositories = self.__get_repositories(api)
        repo_dir = self.output_dir + "/repositories"
        os.makedirs(repo_dir, exist_ok=True)
        logging.debug(f'Repositories dir is {repo_dir}')
        self.__save_repositories(self.repositories, repo_dir, api)

    def __get_repositories(self, api):
        return [repo['name'] for repo in api.get_repositories()]

    def __save_repositories(self, repositories, dir, api):
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
            self.__save_main_branch(repository, dir, api)

    def __save_main_branch(self, repository, dir, api):
        branch_name = api.get_main_branch(repository)['default_branch']
        branch_name_path = f'{dir}/{repository}/main_branch.txt'
        with open(branch_name_path, "w+") as f:
            f.write(branch_name)

    def __save_members(self, api, members, dir):
        for member in members:
            status = api.get_member_status(member['login'])
            logging.debug(f'Got status for {member["login"]}: {status}')
            backup_member = {
                "login": member["login"],
                "url": member["url"],
                "html_url": member["html_url"],
                "role": status["role"],
                "state": status["state"]
            }
            with open(f"{dir}/{member['login']}.json", "w+") as member_file:
                logging.debug(f'Save to {dir}/{member["login"]}.json member: {backup_member}')
                json.dump(backup_member, member_file, indent=4)

    def __save_issues(self, api, issues, dir, repo):
        for issue in issues:
            if 'pull' in issue['html_url']:
                continue
            comments = [
                {"comment": comment['body'],
                 "creation_date": comment['created_at'],
                 "creator_login": comment['user']['login']}
                for comment in api.get_comments_for_issue(repo, issue['number'])]
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

    def __save_pulls(self, api, pulls, dir, repo):
        for pull in pulls:
            if 'pull' not in pull['html_url']:
                continue
            comments = [
                {
                    "comment": comment['body'],
                    "creation_date": comment['created_at'],
                    "creator_login": comment['user']['login']
                } for comment in api.get_comments_for_issue(repo, pull['number'])
            ]
            review_comments = []
            for review in api.get_reviews(repo, pull['number']):
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
                    } for comment in api.get_comments_for_pull(repo, pull['number'], review['id'])
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
