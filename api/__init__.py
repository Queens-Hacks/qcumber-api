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
from functools import wraps
from collections import defaultdict
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import DispatcherMiddleware

# The config imports should come before other package modules so other moudles can import it
from api.config import config, ConfigException
from api import middleware
from api import data
from api import repo


url_map = Map()
endpoint_provider_map = {}

urls = url_map.bind('localhost')


def route(path, methods=None):
    """Register a function to be called for an endpoint.

    The function's return data will be jsonified and used as the response.
    """
    methods = methods or ['GET']

    def endpoint_wrapper(func):
        @wraps(func)
        def endpoint_func(*args, **kwargs):
            return func(*args, **kwargs)
        endpoint_provider_map[func.__name__] = endpoint_func
        rule = Rule(path, methods=methods, endpoint=func.__name__)
        url_map.add(rule)
        return endpoint_func
    return endpoint_wrapper


def route_resource(url_root, provider, endpoint):
    """Register a resource to be served over the API"""
    endpoint_provider_map[endpoint] = provider
    for resource_method, http_method, sub_url in provider.routed_methods:
        url = url_root + sub_url
        methods = [http_method]
        endpoint_str = '.'.join((endpoint, resource_method))
        rule = Rule(url, methods=methods, endpoint=endpoint_str)
        url_map.add(rule)


def api_app(environ, start_response):
    """WSGI application mapping requests to endpoints"""
    adapter = url_map.bind_to_environ(environ)
    handler, values = adapter.match()
    request = Request(environ)
    if '.' in handler:  # must be a resource. this is sketch.
        provider_name, method = handler.split('.', 1)
        provider = endpoint_provider_map[provider_name]
        provided_data = getattr(provider, method)(request, **values)
    else:
        provider = endpoint_provider_map[handler]
        provided_data = provider(**values)
    response = Response(data.dumps(provided_data), mimetype='application/json')
    return response(environ, start_response)


@route('/')
def root():
    """Provide links to all available resources"""
    url_methods = defaultdict(set)
    for resource in url_map.iter_rules():
        url_methods[str(resource)].update(resource.methods)
    resources = [{'endpoint': k, 'methods': list(v)} for k, v in sorted(url_methods.items())]
    return resources


# register the resources set up in data
route_resource('/courses', provider=data.course, endpoint='courses')
route_resource('/subjects', provider=data.subject, endpoint='subjects')
route_resource('/instructors', provider=data.instructor, endpoint='instructors')


def get_app():
    """Returns an initialized and middleware-wrapped wsgi application, ready to go"""

    data.Resource.init()

    app = api_app
    app = middleware.FieldLimiter(app)
    app = middleware.JsonifyHttpException(app)
    app = middleware.DataTransformer(app)

    return app
