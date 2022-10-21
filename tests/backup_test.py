import argparse

from backup.main import parse_args, Backup
import pytest


class TestArgs:
    def test_organization(self):
        args_parsed = parse_args(['test_organization'])
        assert args_parsed.organization == 'test_organization'

    def test_empty_organization(self):
        with pytest.raises(argparse.ArgumentError):
            parse_args(['-t', 'token'])

    def test_token(self):
        args_parsed = parse_args(['-t', 'token', 'test_organization'])
        assert args_parsed.organization == 'test_organization'
        assert args_parsed.token == 'token'

    def test_output_dir(self):
        args_parsed = parse_args(['-t', 'token', '-o', 'test_dir', 'test_organization'])
        assert args_parsed.output_dir == 'test_dir'

    def test_default_output_dir(self):
        args_parsed = parse_args(['-t', 'token', 'test_organization'])
        assert args_parsed.output_dir == '.'


class TestBackup:
    def test_bad_dir(self):
        with pytest.raises(AttributeError):
            Backup('token', 'dir', 'organization', None)
