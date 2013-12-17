#!/usr/bin/env python
"""
    manage
    ~~~~~~

    Utilities for working with the Qcumber API app.
"""

import sys
from functools import wraps


def command(func, _funcs={}):
    """Decorate functions with this to register them as commands"""

    # register the command
    func_name = func.__name__.lower()
    if func_name in _funcs:
        raise Exception('Duplicate definition for command {}'.format(func_name))
    _funcs[func_name] = func

    # play nice and leave the command where it was in this script
    @wraps(func)
    def wrapped(*args):
        return func(*args)
    return wrapped


@command
def help():
    """Get usage information about this script"""
    print('\nUsage: {} [command]\n'.format(sys.argv[0]))
    print('Available commands:')
    for name, func in command.__defaults__[0].items():  # _funcs={}
        print(' * {:16s} {}'.format(name, func.__doc__ or ''))
    sys.exit(1)


@command
def init(force=False):
    """Set the api up: clone the data repo, etc."""
    import api
    try:
        api.data.clone(force)
    except api.data.NotEmptyRepoError:
        print('Not deleting {} because it is not empty. Use "force" or choose a different directory'
              .format(api.config['DATA_LOCAL']))
    except api.ConfigException as e:
        print('There was a configuration error: {}'.format(e))


@command
def runserver(host="127.0.0.1", port="5000"):
    """Run a local development server"""
    try:
        port_num = int(port)
    except ValueError:
        print('The port number must be in integer (got "{}")'.format(port))
        sys.exit(1)
    try:
        from werkzeug.serving import run_simple
    except ImportError:
        print('The werkzeug development server could not be imported :(\n'
              'Have you installed requirements ($ pip install -r requirements'
              '.txt) or perhaps forgotten to activate a virtualenv?')
        sys.exit(1)
    from api import app as app
    run_simple(host, port_num, app, use_debugger=True, use_reloader=True)


@command
def clean():
    """Clean up __pycache__ folders (left behind from testing perhaps)"""
    import os
    import shutil
    for root, subfolders, files in os.walk('.'):
        if '__pycache__' in subfolders:
            garbage = os.path.join(root, '__pycache__')
            shutil.rmtree(garbage)


@command
def test(skip_lint=False, cleanup=True):
    """Run the app's test suite. Cleans up after by default."""
    import unittest
    suite = unittest.TestLoader().discover('test')  # get all the tests
    unittest.TextTestRunner(verbosity=2).run(suite)
    if cleanup:
        clean()
    if not skip_lint:
        lint()


@command
def lint():
    """Run pep8 linting to verify conformance with the style spec."""
    import os
    import pep8
    import time
    style = pep8.StyleGuide(max_line_length=119)
    py_files = []
    for root, dirnames, filenames in os.walk('.'):
        py_files += [os.path.join(root, f) for f in filenames if f.endswith('.py')]
    t0 = time.time()
    result = style.check_files(py_files)
    tf = time.time()
    print('Linted {} files in {:.3g}s'.format(len(py_files), tf-t0))
    if result.total_errors > 0:
        print('FAILED (errors={})'.format(result.total_errors))
        sys.exit(1)
    else:
        print('OK')


if __name__ == '__main__':

    # Get the command, or run 'help' if no command is provided
    if len(sys.argv) < 2:
        cmd, args = 'help', []
    else:
        cmd, args = sys.argv[1].lower(), sys.argv[2:]

    # Map the command to a function, falling back to 'help' if it's not found
    funcs = command.__defaults__[0]  # _funcs={}
    if cmd not in funcs:
        print('Command "{}" not found :('.format(cmd))
        cmd, args = 'help', []

    # do it!
    funcs[cmd](*args)
