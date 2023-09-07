import json
import logging
import os
import subprocess
import sys


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
        logging.error("stdout: {}".format(e.output.decode(sys.getfilesystemencoding())))
        logging.error("stderr: {}".format(e.stderr.decode(sys.getfilesystemencoding())))
        raise e


def filter_save(struct, fields, path):
    backup = filter_fields(fields, struct)
    save_json(path, backup)
