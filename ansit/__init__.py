import colorlog
import logging
import sys
import traceback
from argparse import ArgumentParser

from ansit.manifest import Manifest
from ansit import environment
from ansit import util


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
            '%(log_color)s%(levelname)s %(reset)s%(name)s:'
            '%(lineno)d: %(message)s'))
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
    parser.add_argument(
        '--update', '-u',
        action='store_true', dest='update', default=False,
        help='synchronize and apply changes from manifest to environment')
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        '--verbose', '-v',
        action='store_true', dest='verbose', default=False,
        help='verbose output')
    verbosity.add_argument(
        '--quiet', '-q',
        action='store_true', dest='quiet', default=False,
        help='show only errors and criticals')
    subparsers = parser.add_subparsers(
        title='actions',
        dest='action')
    login_parser = subparsers.add_parser(
        'login', help='interactively login to machine')
    login_parser.add_argument('machine', type=str)
    up_parser = subparsers.add_parser(
        'up', help='start machine(s)')
    up_parser.add_argument('machines', type=str, nargs='*')
    destroy_parser = subparsers.add_parser(
        'destroy', help='destroy machine(s)')
    destroy_parser.add_argument('machines', type=str, nargs='*')
    provision_parser = subparsers.add_parser(
        'provision', help='provision machine(s)')
    test_parser = subparsers.add_parser(
        'test', help='run tests on machine(s)')
    test_parser.add_argument('machines', type=str, nargs='*')
    run_parser = subparsers.add_parser(
        'run', help='create environment, run tests and destroy environment')
    run_parser.add_argument(
        '--leave', action='store_true', default=False,
        help='leave machines after tests')
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logging(args)
    env = environment.Environment(
        Manifest.from_file(args.manifest), args.verbose)
    if args.action == 'run':
        env.synchronize()
        env.apply_changes()
        env.up([])
        env.provision()
        env.test()
        if not args.leave:
            env.destroy()
    elif args.update:
        env.synchronize()
        env.apply_changes()
    if args.action == 'login':
        try:
            env.login(args.machine)
        except environment.EnvironmentError as e:
            util.handle_exception(
                e, 'critical', args.verbose)
    if args.action == 'up':
        env.up(args.machines)
    if args.action == 'provision':
        env.provision()
    if args.action == 'test':
        env.test(args.machines)
    if args.action == 'destroy':
        env.destroy(args.machines)
