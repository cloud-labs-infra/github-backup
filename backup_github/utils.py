import json
import logging
import os
import subprocess
import sys
from pathlib import Path


def save_json(path, content):
    mode = "w" if os.path.exists(path) else "w+"
    with open(path, mode) as file:
        logging.debug(f"Save to {file.name}: {content}")
        json.dump(content, file, indent=4)


def filter_fields(fields, src):
    return {field: src[field] if src and field in src else None for field in fields}


def subprocess_handle(func, args):
    try:
        func(args)
    except subprocess.CalledProcessError as e:
        logging.error("Subprocess call error")
        logging.error("exit code: {}".format(e.returncode))
        if e.output:
            logging.error(
                "stdout: {}".format(e.output.decode(sys.getfilesystemencoding()))
            )
            logging.error(
                "stderr: {}".format(e.stderr.decode(sys.getfilesystemencoding()))
            )
        raise e


def filter_save(struct, fields, path):
    backup = filter_fields(fields, struct)
    save_json(path, backup)


def count_sizes(output_dir):
    git = 0
    repo_dir = f"{output_dir}/repos"
    repos = list(os.walk(repo_dir))[0][1]
    for repository in repos:
        git += sum(
            p.stat().st_size
            for p in Path(f"{repo_dir}/{repository}/content").rglob("*")
        )
    meta = sum(p.stat().st_size for p in Path(output_dir).rglob("*")) - git
    return {"git": git, "meta": meta}
