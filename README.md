# GitHub-Backup

## Project description

Application for backing up information about a GitHub organization

## Installation

You can clone this repository and set up the environment directly from the command line using the following command:

```bash
git clone git@github.com:cloud-labs-infra/github-backup.git
cd github-backup
poetry install
```

## Testing

You can run the tests using the following command:

```bash
poetry run pytest --cov=./ --cov-report=xml
```

This command runs all unit tests and calculates coverage

## Usage

CLI Usage is as follows:

    poetry run backup-github [-h] [-t TOKEN] [-o OUTPUT_DIR] [-r REPOSITORY [REPOSITORY ...]] [-i] [-p] [-m]
                                               [--all]
                                               ORGANIZATION_NAME

    Backup a GitHub organization
    
    positional arguments:
      ORGANIZATION_NAME                     github organization name
    
    options:
      -h, --help                            show this help message and exit
      -t TOKEN, --token TOKEN
                                            personal token
      -o OUTPUT_DIR, --output-directory OUTPUT_DIR
                                            directory for backup
      -r REPOSITORY [REPOSITORY ...], --repository REPOSITORY [REPOSITORY ...]
                                            name of repositories to limit backup
      -i, --issues                          run backup of issues
      -p, --pulls                           run backup of pulls
      -m, --members                         run backup of members
      --all                                 run backup of all data


## Backup structure

    .
    └── organization
        ├── members
        │ └── login1
        │     ├── member.json
        │     └── membership.json
        └── repos
            └── repo1
                ├── content
                │ └── repo1.git
                ├── issues
                │ └── 1
                │     ├── assignee.json
                │     ├── comments
                │     ├── issue.json
                │     └── user.json
                ├── pulls
                │ └── 2
                │     ├── assignee.json
                │     ├── base.json
                │     ├── comments
                │     │ └── 1
                │     │     ├── comment.json
                │     │     └── user.json
                │     ├── head.json
                │     ├── pull.json
                │     ├── reviews
                │     │ ├── 1
                │     │ │   ├── review.json
                │     │ │   └── user.json
                │     │ └── 2
                │     │     ├── comments
                │     │     │ └── 1
                │     │     │     ├── comment.json
                │     │     │     └── user.json
                │     │     ├── review.json
                │     │     └── user.json
                │     └── user.json
                └── repo.json

## Project status

The project is currently in a development state