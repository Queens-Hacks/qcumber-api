"""
    api.middleware
    ~~~~~~~~~~~~~~

    blah blah blah
"""

import json
from werkzeug import abort
from werkzeug.wrappers import Request, Response


class BeforeAfterMiddleware(object):
    """A simple middleware base class providing a before/after interface"""

    def __init__(self, app):
        # Keep a reference to the wsgi app we're wrapping
        self.app = app

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

        # finally, blah
        return response(environ, start_response)


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
        self.target = request.accept_mimetypes.best_match(['application/json'])
        if self.target is None:
            abort(406)

    def after(self, request, response):
        body = response.get_data(as_text=True)
        if response.headers.get('Content-Type') != 'application/json':
            warnings.warn('leaving non-JSON data as a string')
            data = body
        else:
            data = json.loads(body)

        if self.target == 'application/json':
            cereal = json.dumps(data)
            response.set_data(cereal)


class FieldLimiter(BeforeAfterMiddleware):
    """Pares response data down to that set by a ?fields= query parameter.
    Assumes JSON response data from app.

    Limit fields by providing fields= query args. EG:
    GET http://whatever/?fields=code&fields=subject

    The limits only work for top-level keys in structured response bodies.
    """

    def before(self, request):
        if 'fields' not in request.args:
            # don't need to limit any fields
            self.skip = True
            return
        self.fields = request.args.getlist('fields')

    def after(self, request, response):
        if getattr(self, 'skip', False):
            return
        body = response.get_data(as_text=True)
        data = json.loads(body)
        # have they asked for fields that don't exist?
        if not all(field in data for field in self.fields):
            abort(400)

        limited_data = {k: v for k, v in data.items() if k in self.fields}
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
