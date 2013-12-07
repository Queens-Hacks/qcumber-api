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
from werkzeug.wrappers import (BaseRequest, AcceptMixin, Request, BaseResponse,
                               Response)
from werkzeug.exceptions import (NotFound, InternalServerError, NotImplemented,
                                 HTTPException)
from werkzeug.routing import Map, Rule


class AcceptRequest(BaseRequest, AcceptMixin):
    pass


class BeforeAfterMiddleware(object):
    """A simple middleware base class providing a before/after inerface"""
    request_wrapper = None
    response_wrapper = None

    def __init__(self, app):
        # Keep a reference to the wsgi app we're wrapping
        self.app = app

    def before(self, request):
        """Do stuff before deferring to the wrapped app."""

    def after(self, request, response):
        """Do more stuff after getting a response from the wrapped app"""

    def __call__(self, environ, start_response):
        """Process a request"""
        # Get the request if we need it, then do our before stuff
        request = self.request_wrapper and self.request_wrapper(environ) or None
        self.before(request)

        # Defer  to the wrapped app, then do our cleanup n stuff
        response = self.response_wrapper and self.response_wrapper.from_app(
                                                    self.app, environ) or None
        self.after(request, response)

        if self.response_wrapper is not None:
            return response(environ, start_response)
        else:
            return self.app(environ, start_response)


class DataTransformer(BeforeAfterMiddleware):
    """Flexible accept, nice and normalized for inernal use.

    Requests:
     * Form-encoded POST requests are transformed to flat key/value json.
     * requests with JSON bodies are passed through

    Responses:
     * JSON-encoded response bodies are transformed to whatever the client
       accepts.
    """
    request_wrapper = AcceptRequest
    response_wrapper = BaseResponse

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
    request_wrapper = BaseRequest
    response_wrapper = BaseResponse
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


class ResourceRouter(object):
    """Provides url routing for the api"""

    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.url_map = Map([])

        for resource in data_provider.RESOURCES:
            endpoint_string = "/" + resource + "/"
            self.url_map.add(Rule(endpoint_string, handler=self.list_handler, resource=resource))
            self.url_map.add(Rule(endpoint_string + "<uid>", handler=self.item_handler, resource=resource))

    def list_handler(self, request, resource):
        if request.method == 'GET':
            item_list = getattr(self.data_provider, resource)
            if item_list is not None:
                return self.render_json({resource: item_list})
            else:
                raise InternalServerError()
        else:
            raise NotImplemented()

    def item_handler(self, request, resource, uid):
        if request.method == 'GET':
            item_list = getattr(self.data_provider, resource)
            if item_list is not None:
                if uid in item_list:
                    return self.render_json(item_list[uid])
                else:
                    raise NotFound()
            else:
                raise InternalServerError()
        else:
            raise NotImplemented()

    def render_json(self, data):
        return Response(json.dumps(data), mimetype='application/json')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            handler, resource, values = adapter.match()
            return (handler)(request, resource, **values)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


class DataProvider(object):
    """Reads data from the yaml files."""

    def __init__(self):
        self.RESOURCES = ['courses', 'secitons', 'subjects', 'instructors']

        for attr in self.RESOURCES:
            setattr(self, attr, [])
        self.read_files()

    def read_files(self):
        assert True
