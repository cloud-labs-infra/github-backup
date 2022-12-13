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
                    logging.warning('Rate limit exceeded')
                    limit = self.get_rate_limit()
                    reset = limit['reset']
                    seconds = reset - time.time() + self.retry_seconds
                    logging.warning(f'Reset is in {seconds} seconds.')
                    if seconds > 0:
                        logging.info(f'Waiting for {seconds} seconds...')
                        time.sleep(seconds)
                        logging.info('Done waiting - resume!')
                except self.ClientError as e:
                    logging.warning(f'Client error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
                except self.ServerError as e:
                    logging.warning(f'Server error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
                except requests.exceptions.Timeout as e:
                    logging.warning(f'Timeout error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
                except requests.exceptions.ConnectionError as e:
                    logging.warning(f'Connection error: {e}. Try to retry in 5 seconds')
                    time.sleep(self.retry_seconds)
            raise Exception(f'Failed for {self.retry_count + 1} times')

        return ret

    def __init__(self, token, organization, output_dir, retry_count=10, retry_seconds=1):
        self.headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + token}
        self.token = token
        self.organization = organization
        self.output_dir = output_dir
        self.retry_count = retry_count
        self.retry_seconds = retry_seconds

    @retry
    def make_request_post(self, url, body):
        resp = requests.post(url, headers=self.headers, json=body)
        logging.info(f'Make request to {url}')
        self.raise_by_status(resp.status_code)
        logging.info('OK')
        return resp.json()

    def invite_member(self, id, role):
        return self.make_request_post('https://api.github.com/orgs/' + self.organization + '/invitations',
                                      {"invitee_id": id, "role": role})

    def create_repository(self, repo_name, private):
        return self.make_request_post('https://api.github.com/orgs/' + self.organization + '/repos',
                                      {"name": repo_name, "description": "",
                                       "homepage": "https://github.com", "private": private})

    def create_issue(self, repo, issue, assignee, user):
        new_issue = self.make_request_post(
            'https://api.github.com/repos/' + self.organization + '/' + repo + '/issues',
            {"title": issue['title'], "body": issue['body']})
        if issue['state'] == 'closed':
            self.make_request_post(
                'https://api.github.com/repos/' + self.organization + '/' + repo + '/issues/' + str(new_issue[
                    'number']),
                {"state": "closed"})
            self.make_request_post(
                'https://api.github.com/repos/' + self.organization + '/' + repo + '/issues/' + str(new_issue[
                    'number']) + '/comments',
                {"body": f"Assignee is {assignee['login']}"})
        elif assignee["login"] != {}:
            self.make_request_post(
                'https://api.github.com/repos/' + self.organization + '/' + repo + '/issues/' + str(new_issue[
                    'number']),
                {"assignees": [assignee["login"]]})

        self.make_request_post(
            'https://api.github.com/repos/' + self.organization + '/' + repo + '/issues/' + str(new_issue[
                'number']) + '/comments',
            {"body": f"Issues created by {user['login']} at {issue['created_at']}"})
        return new_issue

    def create_issue_comment(self, repo, issue, comment, user):
        self.make_request_post(
            'https://api.github.com/repos/' + self.organization + '/' + repo + '/issues/' + str(issue[
                'number']) + '/comments',
            {"body": comment["body"] + f"\nComment created by {user['login']} at {comment['created_at']}"})
