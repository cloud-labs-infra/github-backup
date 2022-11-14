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

    github-backup [-h] [-t TOKEN]
                  [-o OUTPUT_DIRECTORY]
                  [-r REPOSITORIES]
                  ORGANIZATION_NAME

    Backup a github organization

    positional arguments:
      ORGANIZATION_NAME                  github organization

    optional arguments:
      -h, --help                         show this help message and exit
      -t TOKEN, --token TOKEN            personal access
      -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                                         directory at which to backup the repositories
      -r REPOSITORIES, --repository REPOSITORIES
                                         list of names of repositories to limit backup to

## Backup structure

    └── organization_name
        ├── members
        │   ├── member1.json
        │   └── member2.json
        └── repositories
            ├── private-repositories
            │   └── repo_name1
            │       ├── issues
            │       │   ├── 1.json
            │       │   └── 2.json
            │       ├── pulls
            │       │   └── 3.json
            │       ├── repository_content
            │       │   └── ...
            │       └── main_branch.txt
            └── public-repositories
                └── ...

### Members

Members information is stored in the folder `members`.
Schema of ```{login}.json```:

    {
        "type": "object",
        "properties": {
            "login": {
                "type": "string"
            },
            "url": {
                "type": "string",
                "format": "uri",
            },
            "html_url": {
                "type": "string"
            },
            "role": {
                "type": "string",
                "examples": ["member", "admin"]
            },
            "state": {
                "type": "string"
                "examples": ["active"]
            }
        },
        "required": [
            "login",
            "url",
            "html_url",
            "role",
            "state"
        ]
    }

Example:

    {
        "login": "example",
        "url": "https://api.github.com/users/example",
        "html_url": "https://github.com/example",
        "role": "member",
        "state": "active"
    }

### Repository content

Since it is necessary to obtain information about all the contents of the repository,
including all branches, the contents of the repository are obtained using the command `git clone --mirror`

It can be restored later with the command `git push --mirror`

When restoring, there is a problem with the correct definition of the main branch,
so it is additionally saved to a file `main_branch.txt`

### Issues

Issues information is stored in folder `repo_name/issues`. Schema of `{issue_number}.json`:

    {
        "type": "object",
        "properties": {
            "title": {
                "type": "string"
            },
            "description": {
                "type": "string"
            },
            "creation_date": {
                "type": "string",
                "examples": ["\"2020-07-09T00:17:55Z\""]
            },
            "creator_login": {
                "type": "string"
            },
            "status": {
                "type": "string"
                "examples": ["open", "closed]
            },
            "assignee_login": {
                "type": "string"
            },
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "comment": {
                            "type": "string"
                        },
                        "creation_date": {
                            "type": "string",
                            "examples": ["\"2020-07-09T00:17:55Z\""]
                        },
                        "creator_login": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "comment",
                        "creation_date",
                        "creator_login"
                    ]
                }
            }
        },
        "required": [
            "title",
            "description",
            "creation_date",
            "creator_login",
            "status",
            "assignee_login",
            "comments"
        ]
    }

Example:

    {
        "title": "example",
        "description": "example",
        "creation_date": "2022-09-06",
        "creator_login": "creator",
        "status": "open",
        "assignee_login": "assignee"
        "comments": 
            [
                {
                    "comment": "text",
                    "creation_date": "2020-07-09T00:17:55Z",
                    "creator_login": "creator"
                }
             ]
    }

### Pulls

Pulls information is stored in folder `repo_name/pulls`. Schema of `{pull_number}.json`:

    {
        "type": "object",
        "properties": {
            "description": {
                "type": "string"
            },
            "creation date": {
                "type": "string"
            },
            "creator_login": {
                "type": "string"
            },
            "status": {
                "type": "string"
            },
            "assignee_login": {
                "type": "string"
            },
            "from_branch": {
                "type": "string"
            },
            "to_branch": {
                "type": "string"
            },
            "comments": {
                "type": "array",
                "items": {
                        "type": "object",
                        "properties": {
                            "comment": {
                                "type": "string"
                            },
                            "creation date": {
                                "type": "string"
                            },
                            "creator_login": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "comment",
                            "creation date",
                            "creator_login"
                        ]
                    }
            },
            "review_comments": {
                "type": "array",
                "items": {
                        "type": "object",
                        "properties": {
                            "comment": {
                                "type": "string"
                            },
                            "creation date": {
                                "type": "string"
                            },
                            "creator_login": {
                                "type": "string"
                            },
                            "diff": {
                                "type": "string"
                            },
                            "path": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "comment",
                            "creation date",
                            "creator_login",
                            "diff",
                            "path"
                        ]
                    }
            }
        },
        "required": [
            "description",
            "creation date",
            "creator_login",
            "status",
            "assignee_login",
            "from_branch",
            "to_branch",
            "comments",
            "review_comments"
        ]
    }

Example:

    {
        "description": "example",
        "creation date": "2022-09-06",
        "creator_login": "creator",
        "status": "open",
        "assignee_login": "assignee",
        "from_branch": "from",
        "to_branch": "to",
        "comments": 
            [
                {
                    "comment": "text",
                    "creation date": "2022-09-09",
                    "creator_login": "creator"
                }
             ],
        "review_comments": 
            [          
                {
                    "comment": "text",
                    "creation date": "2022-09-09",
                    "creator_login": "creator",
                    "diff": "some diff",
                    "path": "file.txt"
                }
            ]
    }

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Project status

The project is currently in a development state