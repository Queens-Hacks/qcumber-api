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
import warnings
from werkzeug import abort
from werkzeug.wrappers import BaseRequest, AcceptMixin, BaseResponse


class MixinRequest(BaseRequest, AcceptMixin):
    pass


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
        req = MixinRequest(environ)
        target = req.accept_mimetypes.best_match(['application/json'])

        # can we satisfy the accept at all?
        if target is None:
            abort(406)

        # transform body to json
        resp = BaseResponse.from_app(self.app, environ)
        body = resp.get_data(as_text=True)
        if resp.headers.get('Content-Type') != 'application/json':
            warnings.warn('transforming non-JSON data!')
            data = body
        else:
            data = json.loads(body)

        if target == 'application/json':
            serial = json.dumps(data)
            resp.set_data(serial)
            return resp(environ, start_response)


class FieldLimiter(object):
    """Pares response data down to that set by a ?fields= query parameter.
    Assumes JSON response data from app.

    Limit fields by providing fields= query args. EG:
    GET http://whatever/?fields=code&fields=subject

    The limits only work for top-level keys in structured response bodies.
    """
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        request = BaseRequest(environ)
        if 'fields' not in request.args:
            # don't need to limit fields, skip this layer
            return self.app(environ, start_response)
        fields = request.args.getlist('fields')

        # grab the response so we can limit the fields
        response = BaseResponse.from_app(self.app, environ)
        body = response.get_data(as_text=True)

        data = json.loads(body)

        # have they asked for fields that don't exist?
        if not all(field in data for field in fields):
            abort(400)

        # limit the data
        limited_data = {k:v for k, v in data.items() if k in fields}

        # set it as the new body
        cereal = json.dumps(limited_data)
        response.set_data(cereal)
        return response(environ, start_response)
