import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from backup_github.github import GithubAPI
from backup_github.metrics import git_size
from backup_github.utils import filter_save, subprocess_handle


class Backup:
    token = str
    output_dir = str
    organization = str
    repositories = Optional[list]

    def __init__(self, token, organization, output_dir, repositories):
        self.token = token
        self.organization = organization
        self.output_dir = f"{output_dir}/{organization}"
        self.api = GithubAPI(self.token, self.organization, self.output_dir)
        self.repositories = repositories
        if self.repositories is None:
            self.repositories = self.__get_repositories()
        if not os.path.isdir(output_dir):
            logging.warning("Output directory does not exist. It will be created")
            os.mkdir(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def backup_members(self):
        members_dir = f"{self.output_dir}/members"
        os.makedirs(members_dir, exist_ok=True)
        logging.debug(f"Member dir is {members_dir}")
        org_members = self.api.get_members()
        logging.debug(f"Got members {org_members}")
        self.__save_members(org_members, members_dir)

    def backup_pulls(self):
        repo_dir = f"{self.output_dir}/repos"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            pull_dir = f"{repo_dir}/{repo}/pulls"
            os.makedirs(pull_dir, exist_ok=True)
            logging.debug(f"Pulls dir is {pull_dir}")
            pulls = self.api.get_pulls(repo)
            logging.debug(f"Pulls: {pulls}")
            self.__save_pulls(pulls, pull_dir, repo)

    def backup_issues(self):
        repo_dir = f"{self.output_dir}/repos"
        repos = list(os.walk(repo_dir))[0][1]
        for repo in repos:
            issues_dir = f"{repo_dir}/{repo}/issues"
            os.makedirs(issues_dir, exist_ok=True)
            logging.debug(f"Issues dir is {issues_dir}")
            issues = self.api.get_issues(repo)
            logging.debug(f"Issues: {issues}")
            self.__save_issues(issues, issues_dir, repo)

    def backup_repositories(self):
        repo_dir = f"{self.output_dir}/repos"
        os.makedirs(repo_dir, exist_ok=True)
        logging.debug(f"Repositories dir is {repo_dir}")
        logging.debug(f"Repositories: {self.repositories}")
        self.__save_repositories(self.repositories, repo_dir)

    def __get_repositories(self):
        return [repo["name"] for repo in self.api.get_repositories()]

    def __save_repositories(self, repositories, dir):
        for repository in repositories:
            if self.api.get_repository(repository)["size"] == 0:
                continue
            if not self.__save_repo_content(repository, dir):
                continue
            repo = self.api.get_repository(repository)
            filter_save(
                repo,
                ["id", "name", "private", "fork", "default_branch", "visibility"],
                f"{dir}/{repository}/repo.json",
            )
            git_size.labels(self.organization).inc(
                sum(
                    p.stat().st_size
                    for p in Path(f"{dir}/{repository}/content").rglob("*")
                )
            )

    def __save_repo_content(self, repository, dir):
        cur_dir = os.getcwd()
        repo_content_path = f"{dir}/{repository}/content"
        if os.path.isdir(repo_content_path):
            logging.info(
                f"Repositories dir {dir}/{repository}/content exists. Will update repository"
            )
            os.chdir(repo_content_path)
        else:
            logging.info(
                f"Repositories dir {dir}/{repository}/content does not exist. Will clone repository"
            )
            os.makedirs(repo_content_path, exist_ok=True)
            os.chdir(repo_content_path)
            repo_url = (
                f"https://{self.token}@github.com/{self.organization}/{repository}.git"
            )
            try:
                subprocess_handle(subprocess.call, ["git", "clone", "--bare", repo_url])
                if not os.path.exists(f"{repository}.git"):
                    time.sleep(10)
                    subprocess_handle(
                        subprocess.call, ["git", "clone", "--bare", repo_url]
                    )
                    if not os.path.exists(f"{repository}.git"):
                        raise subprocess.CalledProcessError(
                            1, ["git", "clone", "--bare", repo_url]
                        )
            except subprocess.CalledProcessError:
                shutil.rmtree(f"{dir}/{repository}")
                logging.error(f"Repository {repository} backup error, will be skipped")
                os.chdir(cur_dir)
                return False
        os.chdir(f"{repository}.git")
        subprocess_handle(subprocess.check_output, ["git", "fetch", "-p"])
        os.chdir(cur_dir)
        return True

    def __save_members(self, members, members_dir):
        for member in members:
            member_dir = f'{members_dir}/{member["login"]}'
            os.makedirs(member_dir, exist_ok=True)
            membership = self.api.get_member_status(member["login"])
            filter_save(member, ["id", "login"], f"{member_dir}/member.json")
            filter_save(membership, ["state", "role"], f"{member_dir}/membership.json")

    def __save_comments(self, comments, outer_dir):
        for comment in comments:
            comment_dir = f'{outer_dir}/comments/{comment["id"]}'
            os.makedirs(comment_dir, exist_ok=True)
            filter_save(
                comment, ["id", "body", "created_at"], f"{comment_dir}/comment.json"
            )
            filter_save(comment["user"], ["login"], f"{comment_dir}/user.json")

    def __save_issues(self, issues, dir, repo):
        for issue in issues:
            if "pull" in issue["html_url"]:
                logging.debug(f"Issue {issue['number']} is pull")
                continue

            issue_dir = f'{dir}/{issue["number"]}'
            os.makedirs(issue_dir, exist_ok=True)
            os.makedirs(f"{issue_dir}/comments", exist_ok=True)

            filter_save(
                issue,
                ["title", "body", "created_at", "state"],
                f"{issue_dir}/issue.json",
            )
            filter_save(issue["assignee"], ["login"], f"{issue_dir}/assignee.json")
            filter_save(issue["user"], ["login"], f"{issue_dir}/user.json")

            self.__save_comments(
                self.api.get_comments_for_issue(repo, issue["number"]),
                issue_dir,
            )

    def __save_pulls(self, pulls, dir, repo):
        for pull in pulls:
            if "pull" not in pull["html_url"]:
                continue

            pull_dir = f'{dir}/{pull["number"]}'
            os.makedirs(pull_dir, exist_ok=True)
            os.makedirs(f"{pull_dir}/comments", exist_ok=True)
            os.makedirs(f"{pull_dir}/reviews", exist_ok=True)

            filter_save(
                pull,
                ["title", "body", "created_at", "state", "merge_commit_sha"],
                f"{pull_dir}/pull.json",
            )
            filter_save(pull["assignee"], ["login"], f"{pull_dir}/assignee.json")
            filter_save(pull["user"], ["login"], f"{pull_dir}/user.json")
            filter_save(pull["head"], ["ref", "sha"], f"{pull_dir}/head.json")
            filter_save(pull["base"], ["ref", "sha"], f"{pull_dir}/base.json")

            self.__save_comments(
                self.api.get_comments_for_issue(repo, pull["number"]),
                pull_dir,
            )
            self.__save_pull_reviews(repo, pull, dir)

    def __save_pull_reviews(self, repo, pull, dir):
        for review in self.api.get_reviews(repo, pull["number"]):
            review_dir = f'{dir}/{pull["number"]}/reviews/{review["id"]}'
            os.makedirs(review_dir, exist_ok=True)
            os.makedirs(f"{review_dir}/comments", exist_ok=True)
            filter_save(
                review,
                ["id", "body", "state", "submitted_at", "commit_id"],
                f"{review_dir}/review.json",
            )
            filter_save(review["user"], ["login"], f"{review_dir}/user.json")

            comments = self.api.get_comments_for_review(
                repo, pull["number"], review["id"]
            )
            for comment in comments:
                comments_dir = f'{review_dir}/comments/{comment["id"]}'
                os.makedirs(comments_dir, exist_ok=True)
                filter_save(
                    comment,
                    [
                        "id",
                        "body",
                        "created_at",
                        "diff_hunk",
                        "path",
                        "position",
                        "original_position",
                        "commit_id",
                        "original_commit_id",
                        "in_reply_to_id",
                    ],
                    f"{comments_dir}/comment.json",
                )
                filter_save(comment["user"], ["login"], f"{comments_dir}/user.json")
