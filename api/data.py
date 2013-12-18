"""
    api.data
    ~~~~~~~~

    Loads data and provides interface for it.
"""

import os
import glob
import json
import yaml
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import NotFound, HTTPException
from werkzeug.routing import Map, Rule
from api import config


class Resource(object):
    """Provides url routing for the api

    Instances of this class are WSGI apps, routed to by a base URL. They are
    responsible for mapping HTTP requests to DataProviders.
    """
    def __init__(self, provider_class):
        self.url_map = Map([
            Rule('/', methods=['GET'], endpoint=self.list_handler),
            Rule('/<uid>/', methods=['GET'], endpoint=self.item_handler)
        ])
        self.provider_class = provider_class

    @property
    def data_map(self):
        try:
            data_map = self._data_map
        except AttributeError:
            self._data_map = data_map = self.provider_class.load_all()
        return data_map

    def list_handler(self, request):
        data_list = list(self.data_map.values())
        return self.render_json(data_list)

    def item_handler(self, request, uid):
        item = self.data_map.get(uid, None)
        if item is None:
            raise NotFound()
        return self.render_json(item)

    def render_json(self, data):
        return Response(json.dumps(data), mimetype='application/json')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            handler, values = adapter.match()
            return (handler)(request, **values)
        except HTTPException as e:
            return e

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)


class DataProvider(dict):
    """Base class for resources.

    Objects of this type are responsible for mapping data to the filesystem.
    One instance is created for each item in `os.listdir` of its `fs_path`.
    """

    fs_path = None  # subclasses must override this

    def __init__(self, path):
        self.path = path
        self.load()

    @classmethod
    def load_all(cls):
        rel_root = os.path.join(config['DATA_LOCAL'], 'data', cls.fs_path)
        fs_things = os.listdir(rel_root)
        loaded = {}
        for fs_thing in fs_things:
            provider = cls(os.path.join(rel_root, fs_thing))
            provider_id = provider.get_id()
            loaded[provider_id] = provider
        return loaded


class Course(DataProvider):
    fs_path = 'courses'

    def load(self):
        course_filename = os.path.join(self.path, 'course.yml')
        term_filenames = glob.glob(os.path.join(self.path, 'term-*.yml'))
        course = yaml.load(open(course_filename))
        course['terms'] = []
        for term_filename in term_filenames:
            term = yaml.load(open(term_filename))
            course['terms'].append(term)
        self.update(course)

    def get_id(self):
        # UGLY HACK (should dereference the subject)
        return self['subject'].rsplit('/')[-1][:len('.yml')].upper() + self['number']


class Subject(DataProvider):
    fs_path = 'subjects'

    def load(self):
        data = yaml.load(open(self.path))
        self.update(data)

    def get_id(self):
        return self['code']


class Instructor(DataProvider):
    fs_path = 'instructors'

    def load(self):
        data = yaml.load(open(self.path))
        self.update(data)

    def get_id(self):
        norm_name = self['name'].lower().replace(' ', '-')
        return norm_name
