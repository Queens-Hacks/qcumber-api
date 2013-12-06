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
from api import dummy_json_app


class TestJsonDummy(TestCase):
    def test_dummy(self):
        c = Client(dummy_json_app, BaseResponse)
        resp = c.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_data(as_text=True),
                         '{"message": "hello world"}')


if __name__ == '__main__':
    from unittest import main
    main()
