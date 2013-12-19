"""
    api
    ~~~

    HTTP endpoints for reading and writing course data for Qcumber,
    the refreshing course catalog for Queen's University.


    The Stack:

    HTTP Server
      WSGI data transformer
        WSGI field limiter
          WSGI resource router
            WSGI resource apps
              DataProviders

"""

import json
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import DispatcherMiddleware

# The config imports should come before other package modules so other moudles can import it
from api.config import config, ConfigException
from api import middleware
from api import data
from api import repo

dispatch_appmap = {
    '/courses': data.Resource(provider_class=data.Course),
    '/subjects': data.Resource(provider_class=data.Subject),
    '/instructors': data.Resource(provider_class=data.Instructor),
}


class RootApp(object):
    """Root app for the api"""
    def __init__(self):
        self.url_map = Map([Rule('/', endpoint=self.root_handler)])

    def root_handler(self, request):
        if request.method == 'GET':
            resources = {"resources": list(dispatch_appmap.keys())}
            return self.render_json(resources)
        else:
            raise NotImplemented()

    def render_json(self, data):
        return Response(json.dumps(data), mimetype='application/json')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return (endpoint)(request, **values)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

app = RootApp()
app = DispatcherMiddleware(app, dispatch_appmap)
app = middleware.FieldLimiter(app)
#app = middleware.DataTransformer(app)
app = middleware.PrettyJSON(app)
