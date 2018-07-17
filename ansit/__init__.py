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
        description='Sophisticated tool for testing configuration managment')
    parser.add_argument(
        '--manifest', '-m', type=str,
        action='store', dest='manifest', required=True,
        help='path to file with manifest')
    args = parser.parse_args()
    manifest = Manifest.from_file(args.manifest)
