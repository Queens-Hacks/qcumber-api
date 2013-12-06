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
from werkzeug.exceptions import NotAcceptable
from api import DataTransformer


def dummy_json_app(environ, start_response):
    """Stupid app that sends a deep message: hello world"""
    data = {'message': 'hello world'}
    response = BaseResponse(json.dumps(data), mimetype='application/json')
    return response(environ, start_response)


class TestDataTransformer(TestCase):

    def setUp(self):
        self.app = DataTransformer(dummy_json_app)

    def test_accept_json(self):
        c = Client(self.app, BaseResponse)
        resp = c.get('/', headers=[('Accept', 'application/json')])

    def test_reject_blah(self):
        c = Client(self.app, BaseResponse)
        with self.assertRaises(NotAcceptable):
            resp = c.get('/', headers=[('Accept', 'blah/blah')])


if __name__ == '__main__':
    from unittest import main
    main()
