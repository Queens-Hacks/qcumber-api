#!/usr/bin/env python
"""
    api
    ~~~

    HTTP endpoints for reading and writing course data for Qcumber,
    the refreshing course catalog for Queen's University.


    The Stack:

    HTTP Server
      WSGI data transformer (form-encoding -> json; json -> (json|xml|yaml|...))
        WSGI field limiter
          WSGI resource router
            WSGI resource app(s)

"""

import json
import warnings
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import (NotFound, InternalServerError, NotImplemented,
                                 HTTPException)
from werkzeug.routing import Map, Rule
from werkzeug.wsgi import DispatcherMiddleware


class ResourceApi(object):
    """Provides url routing for the api"""
    def __init__(self, resource, data_provider):
        self.resource = resource
        self.data_provider = data_provider
        self.url_map = Map([
            Rule('/', endpoint=self.list_handler),
            Rule('/<uid>/', endpoint=self.item_handler)
        ])

    def list_handler(self, request):
        if request.method == 'GET':
            item_list = self.data_provider.get_list(self.resource)
            if item_list is not None:
                return self.render_json({self.resource: item_list})
            else:
                raise InternalServerError()
        else:
            raise NotImplementedError()

    def item_handler(self, request, uid):
        if request.method == 'GET':
            item = self.data_provider.get_item(self.resource, uid)
            if item is not None:
                return self.render_json(item)
            else:
                raise NotFound()
        else:
            raise NotImplementedError()

    def render_json(self, data):
        return Response(json.dumps(data), mimetype='application/json')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            handler, values = adapter.match()
            return (handler)(request, **values)
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
        self.RESOURCES = ['courses', 'sections', 'subjects', 'instructors']

        for attr in self.RESOURCES:
            setattr(self, attr, {})
        self.read_files()

    def read_files(self):
        # mock some data
        self.courses = {
            "ANAT100": {
                "id": "ANAT100",
                "data": "sample data for ANAT100"
            },
            "ANAT200": {
                "id": "ANAT200",
                "data": "More!!! sample data for ANAT200"
            }
        }
        pass

    def get_list(self, resource):
        if hasattr(self, resource):
            return getattr(self, resource).values()
        return None

    def get_item(self, resource, uid):
        if hasattr(self, resource):
            r_dict = getattr(self, resource)
            if uid in r_dict:
                return r_dict[uid]
        return None


def root_app(environ, start_response):
    """Mock of the root app"""
    response = BaseResponse(json.dumps({"root": "yup"}), mimetype='application/json')
    return response(environ, start_response)

data_provider = DataProvider()

course_app = ResourceApi('courses', data_provider)
sections_app = ResourceApi('sections', data_provider)
subjects_app = ResourceApi('subjects', data_provider)
instructors_app = ResourceApi('instructors', data_provider)

app = DispatcherMiddleware(root_app, {
    '/courses': course_app,
    '/sections': sections_app,
    '/subjects': subjects_app,
    '/instructors': instructors_app
})
