from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotImplemented
from qcumberapi.utils import url_map
from qcumberapi import views


class Api(object):

    def dispatch(self, environ, start_response):
        request = Request(environ)
        adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            response = handler(request, **values)
        except NotImplemented as e:
            response = Response('Not yet implemented.')
            response.status_code = 501
        except HTTPException as e:
            response = e
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)
