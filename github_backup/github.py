import logging
import time

import requests


class GithubAPI:
    headers = dict
    token = str
    output_dir = str
    organization = str
    retry_count = int
    retry_seconds = int

    class RateLimitExceededException(Exception):
        def __init__(self, message=None):
            self.message = message
            super().__init__(self.message)

    class ClientError(Exception):
        def __init__(self, message=None):
            self.message = message
            super().__init__(self.message)

    class ServerError(Exception):
        def __init__(self, message=None):
            self.message = message
            super().__init__(self.message)

    def raise_by_status(self, status):
        if status == 403:
            logging.info('Status is 403 - Rate limit exceeded exception')
            raise self.RateLimitExceededException()
        elif status == 404:
            logging.info(f'Status is {status} - Client error: Not found')
            raise self.ClientError()
        elif 400 <= status < 500:
            logging.info(f'Status is {status} - Client error')
            raise self.ClientError()
        elif 500 <= status < 600:
            logging.info(f'Status is {status} - Server error')
            raise self.ServerError()

    def retry(func):
        def ret(self, *args, **kwargs):
            for _ in range(self.retry_count + 1):
                try:
                    return func(self, *args, **kwargs)
                except self.RateLimitExceededException:
                    logging.warning("Rate limit exceeded")
                    limit = self.get_rate_limit()
                    reset = limit["reset"]
                    seconds = reset - time.time() + self.retry_seconds
                    logging.warning(f"Reset is in {seconds} seconds.")
                    if seconds > 0:
                        logging.info(f"Waiting for {seconds} seconds...")
                        time.sleep(seconds)
                        logging.info("Done waiting - resume!")
                except self.ClientError as e:
                    logging.warning(f"Client error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
                except self.ServerError as e:
                    logging.warning(f"Server error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
                except requests.exceptions.Timeout as e:
                    logging.warning(f"Timeout error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
                except requests.exceptions.ConnectionError as e:
                    logging.warning(f"Connection error: {e}. Try to retry in 5 seconds")
                    time.sleep(self.retry_seconds)
            raise Exception(f"Failed for {self.retry_count + 1} times")

        return ret

    def __init__(self, token, organization, output_dir, retry_count=10, retry_seconds=1):
        self.headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token}
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.retry_count = retry_count
        self.retry_seconds = retry_seconds

    @retry
    def make_request(self, url, params=None):
        resp = requests.get(url, headers=self.headers, params=params)
        logging.info(f'Make request to {url}')
        self.raise_by_status(resp.status_code)
        logging.info('OK')
        return resp.json()

    def get_organization(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization)

    def get_members(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/members')

    def get_member_status(self, member_login):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/memberships/' + member_login)

    def get_repo(self, repo_name):
        return self.make_request('https://api.github.com/repos/' + self.organization + '/' + repo_name)

    def get_issues(self, repo_name):
        return self.make_request('https://api.github.com/repos/' + self.organization + '/' + repo_name + '/issues',
                                 {'state': 'all'})

    def get_pulls(self, repo_name):
        return self.make_request('https://api.github.com/repos/' + self.organization + '/' + repo_name + '/pulls',
                                 {'state': 'all'})

    def get_comments_for_issue(self, repo_name, issue_number):
        return self.make_request(
            'https://api.github.com/repos/' + self.organization + '/' + repo_name + '/issues/' + str(
                issue_number) + '/comments')

    def get_reviews(self, repo_name, pull_number):
        return self.make_request(
            'https://api.github.com/repos/' + self.organization + '/' + repo_name + '/pulls/' + str(
                pull_number) + '/reviews')

    def get_comments_for_review(self, repo_name, pull_number, review_id):
        return self.make_request(
            'https://api.github.com/repos/' + self.organization + '/' + repo_name + '/pulls/' + str(
                pull_number) + '/reviews/' + str(review_id) + '/comments')

    def get_repositories(self):
        return self.make_request('https://api.github.com/orgs/' + self.organization + '/repos')

    def get_rate_limit(self):
        return self.make_request('https://api.github.com/rate_limit')["resources"]["core"]
