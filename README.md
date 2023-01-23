# GitHub-Backup

## Project description

Application for backing up and restoring information about a GitHub organization

## Installation

You can clone this repository and set up the environment directly from the command line using the following command:

```bash
git clone https://github.com/cloud-labs-infra/github-backup.git
cd github-backup
make env
```

## Testing

You can run the tests using the following command:

```bash
make test
```

This command runs all unit tests and calculates coverage

## Usage

CLI Usage is as follows:

    python3 github_backup/main.py [-h] [-t TOKEN] [-o OUTPUT_DIR]
               [-r REPOSITORY [REPOSITORY ...]]
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

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Project status

The project is currently in a development state