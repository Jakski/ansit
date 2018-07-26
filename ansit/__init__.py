import colorlog
import logging
import sys
from argparse import ArgumentParser

from ansit.manifest import Manifest
from ansit.environment import EnvironmentError
from ansit.drivers import (
    ProvisionerError,
    ProviderError)


logger = logging.getLogger(__name__)


def configure_logging(args):
    '''Set format and configure logger to use colors, if output is a TTY.'''
    details = ''
    if args.verbose:
        level = logging.DEBUG
        details = '%(name)s:%(lineno)d: '
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    if sys.stdout.isatty():
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s' + details + '%(message)s%(reset)s',
            log_colors={
                'WARNING': 'yellow',
                'CRITICAL': 'red',
                'ERROR': 'red'}))
        logging.basicConfig(
            handlers=[handler],
            level=level)
    else:
        logging.basicConfig(
            format=details + '%(message)s',
            level=level)


def parse_args():
    parser = ArgumentParser(
        description='Sophisticated tool for testing configuration managment')
    parser.add_argument(
        '--manifest', '-m', type=str,
        action='store', dest='manifest', default='ansit.yml',
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
    subparsers.add_parser('provision', help='provision machine(s)')
    test_parser = subparsers.add_parser(
        'test', help='run tests on machine(s)')
    test_parser.add_argument('machines', type=str, nargs='*')
    run_parser = subparsers.add_parser(
        'run', help='create environment, run tests and destroy environment')
    run_parser.add_argument(
        '--leave', action='store_true', default=False,
        help='leave machines after tests')
    return parser.parse_args()


def run_tests(env, machines=None):
    summary = env.test() if machines is None else env.test(machines)
    exit_code = 0
    for machine, results in summary.items():
        for result in results:
            if result[1] is True:
                msg = 'PASSED'
                level = 'info'
            elif result[1] is False:
                msg = 'FAILED'
                level = 'error'
                exit_code = 1
            else:
                msg = 'UNKNOWN'
                level = 'warning'
                exit_code = 1
            getattr(logger, level)('%s:%s: %s' % (machine, result[0], msg))
    return exit_code


def main():
    args = parse_args()
    exit_code = 0
    configure_logging(args)
    env = environment.Environment(Manifest.from_file(args.manifest))
    if args.action == 'run':
        env.synchronize()
        env.up([])
        env.apply_changes()
        env.provision()
        exit_code = run_tests(env)
        if not args.leave:
            env.destroy()
    elif args.update:
        env.synchronize()
        env.apply_changes()
    if args.action == 'login':
        try:
            env.login(args.machine)
        except environment.EnvironmentError as e:
            logger.critical(str(e), exc_info=1)
    if args.action == 'up':
        env.up(args.machines)
    if args.action == 'provision':
        env.provision()
    if args.action == 'test':
        exit_code = run_tests(env, args.machines)
    if args.action == 'destroy':
        env.destroy(args.machines)
    sys.exit(exit_code)
