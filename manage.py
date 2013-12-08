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
def test():
    """Run the app's test suite"""
    import unittest
    suite = unittest.TestLoader().discover('.')  # get all the tests
    unittest.TextTestRunner(verbosity=2).run(suite)


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
