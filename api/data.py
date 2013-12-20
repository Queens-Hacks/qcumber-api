"""
    api.data
    ~~~~~~~~

    Loads data and provides interface for it.
"""

import os
import glob
from functools import wraps, partial
import json
from collections import defaultdict
import yaml
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import NotFound, HTTPException
from werkzeug.routing import Map, Rule
from api import config
import api


def _listdir_id_cleaner(name):
    if name.endswith('.yml'):
        return name[:-len('.yml')]
    return name


class RefEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DataRef):
            return obj.get_link()
        return json.JSONEncoder.default(self, obj)

dumps = partial(json.dumps, cls=RefEncoder)


class DataRef(object):
    """proxy references"""

    def __init__(self, data_ref):
        self.ref_dir, self.ref_data_id = data_ref.split('/', 1)

    def get_link(self):
        api_id = Resource.data_dir_map[self.ref_dir].data_to_api_map[self.ref_data_id]
        return api.urls.build(self.ref_dir + '.item', {'api_id': api_id})


class Resource(object):
    """ """

    data_dir_map = {}
    routed_methods = (('GET', '/', 'index'),
                      ('GET', '/<api_id>/', 'item'))

    def __init__(self, endpoint, data_dir):
        # allow other resource instances to find this one
        self.data_dir_map[data_dir] = self
        self.data_dir = data_dir
        self.data_path = os.path.join(config['DATA_LOCAL'], 'data', data_dir)
        self.data_map = {}
        self.data_to_api_map = {}
        self.load = None
        self.get_api_id = None
        self.keysets = defaultdict(lambda: defaultdict(set))  # dict(dict(set()))

    def loader(self, func):
        self.load = func

    def api_id_getter(self, func):
        self.get_api_id = func

    def init(self):
        self.load_all()
        self.build_maps()

    def build_maps(self):
        for api_id, data in self.data_map.items():
            for key, value in data.items():
                try:
                    self.keysets[key][value].add(api_id)
                except TypeError:
                    pass  # unhashable value or something...

    def load_all(self):
        data_ids = map(_listdir_id_cleaner, os.listdir(self.data_path))
        for data_id in data_ids:
            data = self.load(self, data_id)
            api_id = self.get_api_id(self, data)
            data['link'] = DataRef('/'.join((self.data_dir, data_id)))
            self.data_map[api_id] = data
            self.data_to_api_map[data_id] = api_id

    def index(self, request):
        filter_keys = [key for key in request.args if key in self.keysets]
        if filter_keys:
            filtered = set(self.data_map)  # start with everything
            for key in filter_keys:
                filters = request.args.getlist(key)
                subset = set()
                for filter_val in filters:
                    subset.update(self.keysets[key][filter_val])
                filtered.intersection_update(subset)
            data_list = list(self.data_map[key] for key in filtered)
        else:
            data_list = list(self.data_map.values())
        return data_list

    def item(self, request, api_id):
        try:
            return self.data_map[api_id]
        except KeyError:
            raise NotFound()


course = Resource('course', data_dir='courses')


@course.loader
def load_course(self, data_id):
    course_filename = os.path.join(self.data_path, data_id, 'course.yml')
    term_filenames = glob.glob(os.path.join(self.data_path, data_id, 'term-*.yml'))
    course = yaml.load(open(course_filename))
    course['subject'] = {'link': DataRef(course['subject'])}
    course['terms'] = []
    for term_filename in term_filenames:
        term = yaml.load(open(term_filename))
        course['terms'].append(term)
        for section in term['sections']:
            for timeslot in section['timeslots']:
                instructors = []
                for instructor in timeslot['instructors']:
                    if instructor == 'Staff':
                        instructors.append(instructor)
                    else:
                        instructors.append({'link': DataRef(instructor)})
                timeslot['instructors'] = instructors

    return course


@course.api_id_getter
def get_course_id(self, course):
    return course['number']


subject = Resource('subject', data_dir='subjects')


@subject.loader
def load_subjects(self, data_id):
    filename = os.path.join(self.data_path, data_id) + '.yml'
    data = yaml.load(open(filename))
    return data


@subject.api_id_getter
def get_subject_id(self, subject):
    return subject['code'].lower()


instructor = Resource('instructor', data_dir='instructors')


@instructor.loader
def load_instructor(self, data_id):
    filename = os.path.join(self.data_path, data_id) + '.yml'
    data = yaml.load(open(filename))
    return data


@instructor.api_id_getter
def get_instructor_id(self, instructor):
    norm_name = instructor['name'].lower().replace(' ', '-')
    return norm_name
