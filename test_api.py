#!/
"""
    test_api
    ~~~~~~~~

    Unit testing for the API.

    You can call this script directly, do `$ nosetests` if you've got nose,
    or use the the test command from the manage.py script to run the suite.
"""

from unittest import TestCase
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import BadRequest
from api import dummy_json_app, DataTransformer


class TestJsonDummy(TestCase):
    def test_dummy(self):
        c = Client(dummy_json_app, BaseResponse)
        resp = c.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_data(as_text=True),
                         '{"message": "hello world"}')


class TestDataTransformer(TestCase):

    def setUp(self):
        self.app = DataTransformer(dummy_json_app)

    def test_accept_json(self):
        c = Client(self.app, BaseResponse)
        resp = c.get('/', headers=[('Accept', 'application/json')])

    def test_reject_blah(self):
        c = Client(self.app, BaseResponse)
        with self.assertRaises(BadRequest):
            resp = c.get('/', headers=[('Accept', 'blah/blah')])


if __name__ == '__main__':
    from unittest import main
    main()
