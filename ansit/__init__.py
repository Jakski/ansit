import colorlog
import logging
import sys
from argparse import ArgumentParser

from ansit.manifest import Manifest


logger = logging.getLogger(__name__)


def configure_logging():
    '''Set format and configure logger to use colors, if output is a TTY.'''
    if sys.stdout.isatty():
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s'
            ' %(blue)s%(name)s%(reset)s'
            ':%(blue)s%(lineno)d%(reset)s'
            ': %(message)s'))
        logging.basicConfig(
            handlers=[handler],
            level=logging.INFO)
    else:
        logging.basicConfig(
            format='%(levelname)-8s %(name)s:%(lineno)d: %(message)s',
            level=logging.INFO)


def main():
    configure_logging()
    parser = ArgumentParser(
        description='Sophisticated tool for testing Ansible playbooks')
    parser.add_argument(
        '--manifest', '-m', type=str,
        action='store', dest='manifest', required=True,
        help='path to file with manifest')
    parser.add_argument(
        '--leave-dir',
        action='store_true', dest='leave_dir', default=False,
        help='leave test directory after testing')
    parser.add_argument(
        '--tests-only', '-t',
        action='store_true', dest='tests_only', default=False,
        help='run only tests')
    parser.add_argument(
        '--leave-machines', '-l',
        action='store_true', dest='leave_machines', default=False,
        help='leave machines running after tests. It will also'
             ' leave test directory like --leave-dir.')
    args = parser.parse_args()
    manifest = Manifest.from_file(args.manifest)
