#!/usr/bin/env python
"""
    api
    ~~~

    HTTP endpoints for reading and writing course data for Qcumber,
    the refreshing course catalog for Queen's University.


    Here is my (phil) proposed layering of the app stack:

    HTTP nginx
      SOCK gunicorn
        WSGI data transformer (form-encoding -> json; json -> (json|xml|yaml|...))
          WSGI field limiter
            WSGI resource router (course|subject|instructor...)
              WSGI resource app

"""

import json
from werkzeug.wrappers import Response


def dummy_json_app(environ, start_response):
    """Stupid app that sends a deep message: hello world"""
    data = {'message': 'hello world'}
    response = Response(json.dumps(data), mimetype='application/json')
    return response(environ, start_response)


class DataTransformer(object):
    """Flexible accept, nice and normalized for inernal use.

    Requests:
     * Form-encoded POST requests are transformed to flat key/value json.
     * requests with JSON bodies are passed through

    Responses:
     * JSON-encoded response bodies are transformed to whatever the client
       accepts.
    """

    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):

        def _start_response(status, headers, *args, **kwargs):
            return start_response(status, headers, *args, **kwargs)
        return self.app(environ, _start_response)


class FieldLimiter(object):
    """Pares response data down to that set by a ?fields= query parameter.
    Assumes JSON response data from app.
    """
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        return self.app(environ, start_response)

