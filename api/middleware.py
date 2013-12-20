"""
    api.middleware
    ~~~~~~~~~~~~~~

    blah blah blah
"""

import json
from werkzeug.local import Local, release_local
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import BadRequest, NotAcceptable, HTTPException, abort


class BeforeAfterMiddleware(object):
    """A simple middleware base class providing a before/after interface.

    A werkzeug.Local instance called `local` is bound to the middleware for
    saving state in a thread-safe way between the `before` and `after` calls.
    """

    def __init__(self, app):
        # Keep a reference to the wsgi app we're wrapping
        super(BeforeAfterMiddleware, self).__setattr__('app', app)
        super(BeforeAfterMiddleware, self).__setattr__('local', Local())

    def before(self, request):
        """Do stuff before deferring to the wrapped app."""

    def after(self, request, response):
        """Do more stuff after getting a response from the wrapped app"""

    def __call__(self, environ, start_response):
        """Process a request"""
        # Set up the request and do our pre-processing
        request = Request(environ)
        self.before(request)

        # Defer  to the wrapped app, then do our cleanup n stuff
        response = Response.from_app(self.app, environ)
        self.after(request, response)
        release_local(self.local)

        # finally, blah
        return response(environ, start_response)

    def mutate_error(self, *args, **kwargs):
        raise TypeError('Mutating a BeforeAfterMiddleware is (usually) not thread-safe. '
                        'Use the thread-safe `self.local` property.')

    __setattr__ = mutate_error

    __delattr__ = mutate_error


class DataTransformer(BeforeAfterMiddleware):
    """Flexible accept, nice and normalized for internal use.

    Requests:
     * Form-encoded POST requests are transformed to flat key/value json.
     * requests with JSON bodies are passed through

    Responses:
     * JSON-encoded response bodies are transformed to whatever the client
       accepts.
    """

    def before(self, request):
        self.local.target = request.accept_mimetypes.best_match(['application/json'])
        if self.local.target is None:
            raise NotAcceptable()

    def after(self, request, response):
        body = response.get_data(as_text=True)
        if response.headers.get('Content-Type') != 'application/json':
            warnings.warn('leaving non-JSON data as a string')
            data = body
        else:
            data = json.loads(body)

        if self.local.target == 'application/json':
            cereal = json.dumps(data)
            response.set_data(cereal)


class FieldLimiter(BeforeAfterMiddleware):
    """Pares response data down to that set by a ?field= query parameter.
    Assumes JSON response data from app.

    Limit fields by providing field= query args. EG:
    GET http://whatever/?field=code&field=subject

    The limits only work for top-level keys in structured response bodies.
    """

    def limit(self, data, fields):
        # have they asked for fields that don't exist?
        if not all(field in data for field in fields):
            raise BadRequest()
        limited = {key: data[key] for key in fields}
        return limited

    def after(self, request, response):
        if 'field' not in request.args:
            return

        fields = [s.lower() for s in request.args.getlist('field')]

        body = response.get_data(as_text=True)
        data = json.loads(body)

        if isinstance(data, list):
            limited_data = [self.limit(d, fields) for d in data]
        else:
            limited_data = self.limit(data, fields)

        cereal = json.dumps(limited_data)
        response.set_data(cereal)


class PrettyJSON(BeforeAfterMiddleware):
    """Prettify JSON responses"""

    def after(self, request, response):
        if response.headers.get('Content-Type') == 'application/json':
            body = response.get_data(as_text=True)
            data = json.loads(body)
            pretty_data = json.dumps(data, indent=2)
            response.set_data(pretty_data)


class JsonifyHttpException(object):
    """Format http errors as json, but keep the error status in the response

    Should wrap the highest level possible so that any errors thrown in nested
    wrapped apps will be caught.
    """

    def __init__(self, app, error_prefixes=[4, 5]):
        # Keep a reference to the wsgi app we're wrapping
        self.app = app
        self.local = Local()
        self.error_prefixes = error_prefixes

    def jsonify_error(self, http_err, environ):
        """Creates a error response with body as json"""
        data = {
            'status code': http_err.code,
            'error name': http_err.name,
            'description': http_err.description
        }

        response = http_err.get_response(environ)
        response.data = json.dumps(data)
        response.headers['content-type'] = 'application/json'

        return response

    def __call__(self, environ, start_response):
        """Process a request"""
        try:
            # Set up the request
            request = Request(environ)

            # Defer  to the wrapped app, then do our cleanup
            response = Response.from_app(self.app, environ)

            if response.status_code/100 in self.error_prefixes:
                abort(response.status_code)

            release_local(self.local)

            return response(environ, start_response)

        except HTTPException as err:
            response = self.jsonify_error(err, environ)
            return response(environ, start_response)
