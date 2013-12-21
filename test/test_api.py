"""
    test_api
    ~~~~~~~~

    Unit testing for the API.

    You can call this script directly, do `$ nosetests` if you've got nose,
    or use the the test command from the manage.py script to run the suite.
"""

import os
import json
import shutil
import tarfile
import tempfile
from unittest import TestCase
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import NotAcceptable, BadRequest, NotFound

import api
from api.config import (
    REQUIRED,
    variables,
    ConfigException,
    _GetitemProxy,
    get_config,
)
from api.repo import (
    NotEmptyRepoError,
    clone,
)
from api.middleware import (
    BeforeAfterMiddleware,
    DataTransformer,
    FieldLimiter,
    JsonifyHttpException,
)

test_data = {'message': 'hello world', 'errors': []}
json_resp = lambda resp: json.loads(resp.get_data(as_text=True))


def dummy_json_app(environ, start_response):
    """Stupid app that sends a deep message: hello world"""
    response = BaseResponse(json.dumps(test_data), mimetype='application/json')
    return response(environ, start_response)


def not_found_app(environ, start_response):
    raise NotFound


def bad_request_app(environ, start_response):
    raise BadRequest


class TestConfig(TestCase):

    def test_module_proxy(self):
        class FakeConfigModule(object):
            """fake a config module with an object, since we only getattr on it"""
            CONFIG_SETTING = 'hello'
        module = FakeConfigModule()
        proxy = _GetitemProxy(module)
        var = proxy['CONFIG_SETTING']
        self.assertEqual(var, 'hello')
        with self.assertRaises(KeyError):
            proxy['BAD_SETTING']

    def test_get_config(self):
        variables = (('CONFIG_SETTING', REQUIRED, ''),
                     ('CONFIG_OPTIONAL', 'default', ''),)

        source = dict(CONFIG_SETTING='hello')
        config = get_config(variables, source)
        self.assertEqual(config['CONFIG_SETTING'], 'hello')
        self.assertEqual(config['CONFIG_OPTIONAL'], 'default')

        source = dict(CONFIG_SETTING='hello', CONFIG_OPTIONAL='override')
        config = get_config(variables, source)
        self.assertEqual(config['CONFIG_SETTING'], 'hello')
        self.assertEqual(config['CONFIG_OPTIONAL'], 'override')

        with self.assertRaises(ConfigException):
            variables = (('CONFIG_SETTING', REQUIRED, ''),)
            source = dict()
            config = get_config(variables, source)


class TestData(TestCase):
    local_repo = os.path.join(os.getcwd(), 'test', 'test_repo')

    @classmethod
    def setUpClass(cls):
        with tarfile.open('{}.tar'.format(cls.local_repo)) as t:
            t.extractall()

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        api.config.update(DATA_REMOTE=self.local_repo,
                          DATA_LOCAL=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.local_repo)

    def test_clone(self):
        clone()
        self.assertTrue(os.path.isdir(os.path.join(self.temp_dir, '.git')))
        with self.assertRaises(NotEmptyRepoError):
            clone()


class TestMiddlewareBase(TestCase):

    def setUp(self):
        def app(environ, start_response):
            self.order.append('app_call')
            response = BaseResponse(json.dumps(test_data))
            return response(environ, start_response)
        self.order = []
        self.app = app

    def test_passthrough_mw(self):
        app = BeforeAfterMiddleware(dummy_json_app)
        c = Client(app, BaseResponse)
        response = c.get('/')
        self.assertEqual(json_resp(response), test_data)

    def test_before_comes_first(self):
        test_self = self

        class BeforeMW(BeforeAfterMiddleware):
            def before(self, request):
                test_self.order.append('before')

        wrapped = BeforeMW(self.app)
        c = Client(wrapped, BaseResponse)
        c.get('/')
        self.assertEqual(self.order, ['before', 'app_call'])

    def test_after_comes_last(self):
        test_self = self

        class AfterMW(BeforeAfterMiddleware):
            def after(self, request, response):
                test_self.order.append('after')
        wrapped = AfterMW(self.app)
        c = Client(wrapped, BaseResponse)
        c.get('/')
        self.assertEqual(self.order, ['app_call', 'after'])

    def test_mw_is_immutable(self):
        """Practice safe threading"""
        class MW(BeforeAfterMiddleware):
            def before(self):
                self.some_property = 'aaaah'
        wrapped = MW(dummy_json_app)
        c = Client(wrapped, BaseResponse)
        with self.assertRaises(TypeError):
            c.get('/')
        with self.assertRaises(TypeError):
            del wrapped.some_property


class TestDataTransformer(TestCase):

    def setUp(self):
        self.app = DataTransformer(dummy_json_app)

    def test_accept_json(self):
        c = Client(self.app, BaseResponse)
        resp = c.get('/', headers=[('Accept', 'application/json')])
        self.assertEqual(json_resp(resp), test_data)

    def test_reject_blah(self):
        c = Client(self.app, BaseResponse)
        with self.assertRaises(NotAcceptable):
            resp = c.get('/', headers=[('Accept', 'blah/blah')])


class TestFieldLimiter(TestCase):

    def setUp(self):
        app = FieldLimiter(dummy_json_app)
        self.client = Client(app, BaseResponse)

    def test_no_limiting(self):
        resp = self.client.get('/')
        self.assertEqual(json_resp(resp), test_data)

    def test_limit_one(self):
        resp = self.client.get('/?field=message')
        self.assertEqual(json_resp(resp), {'message': test_data['message']})

    def test_limit_multi(self):
        fields = ('message', 'errors')
        resp = self.client.get('/?field={}&field={}'.format(*fields))
        expecting = {k: v for k, v in test_data.items() if k in fields}
        self.assertEqual(json_resp(resp), expecting)

    def test_limit_bad(self):
        with self.assertRaises(BadRequest):
            resp = self.client.get('/?field=nonexistentfield')

    def test_list_limit(self):
        def app(environ, start_response):
            """Stupid app that sends a deep message: hello world"""
            response = BaseResponse(json.dumps([test_data] * 2),
                                    mimetype='application/json')
            return response(environ, start_response)
        wrapped = FieldLimiter(app)
        c = Client(wrapped, BaseResponse)
        resp = c.get('/?field=message')
        self.assertEqual(json_resp(resp), [{'message': test_data['message']}] * 2)


class TestJsonifyHttpException(TestCase):

    def test_404_as_json(self):
        app = JsonifyHttpException(not_found_app)
        client = Client(app, BaseResponse)

        response = client.get('/nothingtofind')
        self.assertEqual(response.headers['Content-Type'], 'application/json')

    def test_bad_request_as_json(self):
        app = JsonifyHttpException(bad_request_app)
        client = Client(app, BaseResponse)

        response = client.get('/alwaysbad')
        self.assertEqual(response.headers['Content-Type'], 'application/json')


class TestAPIApp(TestCase):

    def setUp(self):
        self.app = api.api_app
        self.client = Client(self.app, BaseResponse)

    def test_status_ok(self):
        response = self.client.get('/', headers=[('Accept', 'application/json')])
        self.assertEqual(response.status_code, 200)

    def test_status_not_found(self):
        with self.assertRaises(NotFound):
            response = self.client.get('/notaresource')
