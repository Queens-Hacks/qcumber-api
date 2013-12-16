#!/
"""
    test_api
    ~~~~~~~~

    Unit testing for the API.

    You can call this script directly, do `$ nosetests` if you've got nose,
    or use the the test command from the manage.py script to run the suite.
"""

import json
from unittest import TestCase
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import NotAcceptable, BadRequest

from api.middleware import (
    BeforeAfterMiddleware,
    DataTransformer,
    FieldLimiter,
)


test_data = {'message': 'hello world', 'errors': []}
json_resp = lambda resp: json.loads(resp.get_data(as_text=True))


def dummy_json_app(environ, start_response):
    """Stupid app that sends a deep message: hello world"""
    response = BaseResponse(json.dumps(test_data), mimetype='application/json')
    return response(environ, start_response)


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
        """Practic safe threading"""
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


if __name__ == '__main__':
    from unittest import main
    main()
