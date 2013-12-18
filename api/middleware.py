"""
    api.middleware
    ~~~~~~~~~~~~~~

    blah blah blah
"""

import json
from werkzeug.local import Local, release_local
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import BadRequest, NotAcceptable


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
    """Flexible accept, nice and normalized for inernal use.

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

    def before(self, request):
        if 'field' not in request.args:
            # don't need to limit any fields
            self.local.skip = True
        else:
            self.local.fields = request.args.getlist('field')

    def limit(self, data):
        # have they asked for fields that don't exist?
        if not all(field in data for field in self.local.fields):
            raise BadRequest()
        limited = {k: v for k, v in data.items() if k in self.local.fields}
        return limited

    def after(self, request, response):
        if getattr(self.local, 'skip', False):
            return
        body = response.get_data(as_text=True)
        data = json.loads(body)

        if isinstance(data, list):
            limited_data = [self.limit(d) for d in data]
        else:
            limited_data = self.limit(data)

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
