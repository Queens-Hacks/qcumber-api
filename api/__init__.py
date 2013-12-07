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


class AcceptRequest(BaseRequest, AcceptMixin):
    pass


class BeforeAfterMiddleware(object):
    """A simple middleware base class providing a before/after inerface"""
    request_wrap = None
    response_wrap = None

    def __init__(self, app):
        self.app = app

    def before(self, request):
        pass

    def after(self, request, response):
        pass

    def __call__(self, environ, start_response):
        if self.request_wrap is not None:
            request = self.request_wrap(environ)
        self.before(request)

        if self.response_wrap is not None:
            response = self.response_wrap.from_app(self.app, environ)
        self.after(request, response)

        if self.response_wrap is not None:
            return response(environ, start_response)
        else:
            return app(environ, start_response)


class DataTransformer(BeforeAfterMiddleware):
    """Flexible accept, nice and normalized for inernal use.

    Requests:
     * Form-encoded POST requests are transformed to flat key/value json.
     * requests with JSON bodies are passed through

    Responses:
     * JSON-encoded response bodies are transformed to whatever the client
       accepts.
    """
    request_wrap = AcceptRequest
    response_wrap = BaseResponse

    def before(self, request):
        self.target = request.accept_mimetypes.best_match(['application/json'])
        if self.target is None:
            abort(406)

    def after(self, request, response):
        body = response.get_data(as_text=True)
        if response.headers.get('Content-Type') != 'application/json':
            warnings.warn('leaving non-JSON datak as a string')
            data = body
        else:
            data = json.loads(body)

        if self.target == 'application/json':
            cereal = json.dumps(data)
            response.set_data(cereal)


class FieldLimiter(BeforeAfterMiddleware):
    """Pares response data down to that set by a ?fields= query parameter.
    Assumes JSON response data from app.

    Limit fields by providing fields= query args. EG:
    GET http://whatever/?fields=code&fields=subject

    The limits only work for top-level keys in structured response bodies.
    """
    request_wrap = BaseRequest
    response_wrap = BaseResponse
    def before(self, request):
        if 'fields' not in request.args:
            # don't need to limit any fields
            self.skip = True
            return
        self.fields = request.args.getlist('fields')


    def after(self, request, response):
        if getattr(self, 'skip', False):
            return
        body = response.get_data(as_text=True)
        data = json.loads(body)
        # have they asked for fields that don't exist?
        if not all(field in data for field in self.fields):
            abort(400)

        limited_data = {k:v for k, v in data.items() if k in self.fields}
        cereal = json.dumps(limited_data)
        response.set_data(cereal)
