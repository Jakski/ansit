import colorlog
import logging
import sys
from argparse import ArgumentParser

from ansit.manifest import Manifest


logger = logging.getLogger(__name__)


def configure_logging(args):
    '''Set format and configure logger to use colors, if output is a TTY.'''
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    if sys.stdout.isatty():
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s'
            ' %(blue)s%(name)s%(reset)s'
            ':%(blue)s%(lineno)d%(reset)s'
            ': %(message)s'))
        logging.basicConfig(
            handlers=[handler],
            level=level)
    else:
        logging.basicConfig(
            format='%(levelname)-8s %(name)s:%(lineno)d: %(message)s',
            level=level)


def parse_args():
    parser = ArgumentParser(
        description='Sophisticated tool for testing configuration managment')
    parser.add_argument(
        '--manifest', '-m', type=str,
        action='store', dest='manifest', required=True,
        help='path to file with manifest')
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        '--verbose', '-v',
        action='store_true', dest='verbose', default=False,
        help='verbose output')
    verbosity.add_argument(
        '--quiet', '-q',
        action='store_true', dest='quiet', default=False,
        help='show only errors and criticals')
    subparsers = parser.add_subparsers(title='actions')
    login_parser = subparsers.add_parser(
        'login', help='interactively login to machine')
    login_parser.add_argument(
        'machine', type=str, metavar='login_machine')
    up_parser = subparsers.add_parser(
        'up', help='start machine(s)')
    up_parser.add_argument(
        'up_machines', type=str,
        nargs='*', metavar='machines')
    destroy_parser = subparsers.add_parser(
        'destroy', help='destroy machine(s)')
    destroy_parser.add_argument(
        'destroy_machines', type=str,
        nargs='*', metavar='machines')
    provision_parser = subparsers.add_parser(
        'provision', help='provision machine(s)')
    provision_parser.add_argument(
        'provision_machines', type=str,
        nargs='*', metavar='machines')
    test_parser = subparsers.add_parser(
        'test', help='run tests on machine(s)')
    test_parser.add_argument(
        'test_machines', type=str,
        nargs='*', metavar='machines')
    run_parser = subparsers.add_parser(
        'run', help='create environment, run tests and destroy environment')
    run_parser.add_argument(
        '--leave', action='store_true', default=False,
        help='leave machines after tests')
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logging(args)
    manifest = Manifest.from_file(args.manifest)
