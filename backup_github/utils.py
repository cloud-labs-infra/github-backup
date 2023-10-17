import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import boto3 as boto3


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


def upload_to_s3(ak, sk, endpoint, backup_dir, bucket, organization):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        endpoint_url=endpoint,
        verify=False
    )
    shutil.make_archive(base_name="backup_archive", format="gztar", root_dir=backup_dir)
    resp = s3.upload_file(
        "./backup_archive.tar.gz",
        bucket,
        f'{organization}-{datetime.now().strftime("%m-%d-%Y_%H-%M")}.tar.gz',
    )
    if resp.status >= 300:
        logging.error(f"Uploading of backup failed, error message: {resp.errorMessage}")
        raise Exception(resp.errorMessage)
    logging.info("Backup is loaded")
