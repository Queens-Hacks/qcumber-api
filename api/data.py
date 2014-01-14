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
import api


class RefEncoder(json.JSONEncoder):
    """Encode json with embedded DataRef instances."""
    def default(self, obj):
        if isinstance(obj, DataRef):
            return obj.get_link()
        return json.JSONEncoder.default(self, obj)

# custom json serializer that knows how to encode RefEncoders
dumps = partial(json.dumps, cls=RefEncoder)


class DataRef(object):
    """Create a reference to some data from other data.

    This class keeps track of the reference so that it can be looked up later,
    after all the data has been loaded.

    References in the data files are of the format:
    ref: {type}/{id}
    """

    def __init__(self, data_ref):
        self.ref = data_ref
        self.ref_dir, self.ref_data_id = self.ref.split('/', 1)

    def get_link(self):
        """Returns an api uri for the resource"""
        data = Resource.data_ref_map[self.ref]
        provider = Resource.data_provider_map[self.ref_dir]
        api_id = provider.get_api_id(provider, data)
        link = api.urls.build(self.ref_dir + '.item', {'api_id': api_id})
        return link

    def get(self):
        """Returns the actual referenced resource"""
        data = Resource.data_ref_map[self.ref]
        return data


class Resource(object):
    """"""
    data_path = os.path.join(api.config['DATA_LOCAL'], 'data')
    data_provider_map = {}  # maps provider names to providers
    data_ref_map = {}  # map filesystem references to data
    routed_methods = (('index', 'GET', '/'),
                      ('item',  'GET', '/<api_id>/'))

    @classmethod
    def init(cls):
        """Sets up all the instances of this class.

        Resources have three stages of initalization, and all resources should
        complete each stage before moving on to the next one to avoid reference
        dependency issues.
        """
        for provider in cls.data_provider_map.values():
            provider.load_data()
        for provider in cls.data_provider_map.values():
            provider.map_api_ids()
        for provider in cls.data_provider_map.values():
            provider.build_maps()

    def __init__(self, endpoint, data_dir):
        self.api_id_map = {}  # map api ids to data
        self.data_dir = data_dir  # let the class know about itself
        self.data_provider_map[data_dir] = self  # let other instances find this one
        self.keysets = defaultdict(lambda: defaultdict(set))  # filter query by top-level keys dict(dict(set()))
        self.load = None
        self.get_api_id = None

    def loader(self, func):
        """Decorate a function to be used as a data loader for this resource"""
        self.load = func

    def api_id_getter(self, func):
        """Decorate a function to compute the api id for this resource"""
        self.get_api_id = func

    def filename_to_ref(self, filename):
        """Normalize filesystem listings which may be files or directories"""
        if filename.endswith('.yml'):
            filename = filename[:-len('.yml')]
        ref = os.path.join(self.data_dir, filename)
        return ref

    def load_data(self):
        """Load all the data for this resource into memory.

        The individual pieces of data are referenced in a mapping from their
        data reference.
        """
        data_path = os.path.join(self.data_path, self.data_dir)
        data_refs = map(self.filename_to_ref, os.listdir(data_path))
        for data_ref in data_refs:
            data = self.load(self, data_ref)
            data.update(link=DataRef(data_ref))
            self.data_ref_map[data_ref] = data

    def map_api_ids(self):
        """Populate a mapping from api ids to data instances for this resource.

        This method should be called after `load_data` has been called on all
        the Resource instances, so that any Resource wishing to dereference
        another piece of data in order to build its api id can be sure it has
        been loaded.
        """
        resource_data = (self.data_ref_map[k] for k in self.data_ref_map if k.startswith(self.data_dir))
        for data in resource_data:
            api_id = self.get_api_id(self, data)
            data['uid'] = api_id
            self.api_id_map[api_id] = data

    def build_maps(self):
        """Generate maps of maps to sets of api_ids for query limiting.

        For every top-level key with a hashable value in a resource's set of
        data, a mapping is created for every value for that key to the set of
        data that have that value.

        so like, for this data

        data:
            stuff/1: {fruit: apple, colour: red}
            stuff/2: {fruit: apple, colour: green}

        you get a mapping like this

        fruit:
            apple: set(stuff/1, stuff/2)
        colour:
            red: set(stuff/1)
            green: set(stuff/2)

        The mapping is built for every top-level key in the data that has a
        hashable value.
        """
        for api_id, data in self.api_id_map.items():
            for key, value in data.items():
                value_key = value
                # if value is a proper nested object the unique id
                if isinstance(value, dict):
                    if 'link' in value:
                        value_key = value['link'].get()['uid']
                try:
                    self.keysets[key][value_key].add(api_id)
                except TypeError:
                    pass  # unhashable value or something...

    def index(self, request):
        """List the data for this resource

        The request's query string can be used to limit the result. For example,
        the query string `?colour=red` will limit the list to those items who
        have a top-level key called `colour` with a value `red`.
        """
        filter_keys = [key for key in request.args if key in self.keysets]
        if filter_keys:
            filtered = set(self.api_id_map)  # start with everything
            for key in filter_keys:
                filters = request.args.getlist(key)
                subset = set()
                for filter_val in filters:
                    subset.update(self.keysets[key][filter_val])
                filtered.intersection_update(subset)
            data_list = list(self.api_id_map[key] for key in filtered)
        else:
            data_list = list(self.api_id_map.values())
        return data_list

    def item(self, request, api_id):
        """Retrieve a sinle piece of data by its id"""
        try:
            return self.api_id_map[api_id]
        except KeyError:
            raise NotFound()


course = Resource('course', data_dir='courses')


@course.loader
def load_course(self, data_ref):
    course_filename = os.path.join(self.data_path, data_ref, 'course.yml')
    term_filenames = glob.glob(os.path.join(self.data_path, data_ref, 'term-*.yml'))
    course = yaml.load(open(course_filename))
    course['subject'] = {'link': DataRef(course['subject']['ref'])}
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
                        instructors.append({'link': DataRef(instructor['ref'])})
                timeslot['instructors'] = instructors

    return course


@course.api_id_getter
def get_course_id(self, course):
    code = course['subject']['link'].get()['code']
    course_id = '{}-{}'.format(code.lower(), course['number'])
    return course_id


subject = Resource('subject', data_dir='subjects')


@subject.loader
def load_subjects(self, data_ref):
    filename = os.path.join(self.data_path, data_ref) + '.yml'
    data = yaml.load(open(filename))
    return data


@subject.api_id_getter
def get_subject_id(self, subject):
    return subject['code'].lower()


instructor = Resource('instructor', data_dir='instructors')


@instructor.loader
def load_instructor(self, data_ref):
    filename = os.path.join(self.data_path, data_ref) + '.yml'
    data = yaml.load(open(filename))
    return data


@instructor.api_id_getter
def get_instructor_id(self, instructor):
    norm_name = instructor['name'].lower().replace(' ', '-')
    return norm_name
