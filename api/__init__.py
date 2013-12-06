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
from werkzeug.wrappers import Response, Request
from werkzeug.exceptions import NotFound, InternalServerError, NotImplemented, HTTPException
from werkzeug.routing import Map, Rule


def dummy_json_app(environ, start_response):
    """Stupid app that sends a deep message: hello world"""
    data = {'message': 'hello world'}
    response = Response(json.dumps(data), mimetype='application/json')
    return response(environ, start_response)


class DataTransformer(object):

    """Flexible accept, nice and normalized for internal use.

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
