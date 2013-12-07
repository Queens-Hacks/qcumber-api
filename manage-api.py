#!/usr/bin/env python
from werkzeug import script


def make_app():
    from qcumberapi.app import Api
    return Api()

action_runserver = script.make_runserver(make_app, use_reloader=True)

script.run()
