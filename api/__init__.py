#!/usr/bin/env python
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
from werkzeug.wrappers import Response
from werkzeug.wsgi import DispatcherMiddleware

# The config imports should come before other package modules so other moudles can import it
from api.config import config, ConfigException
from api import middleware
from api import data
from api import repo


dispatch_appmap = {
    '/courses': data.Resource(url_root='/courses', provider_class=data.Course),
    '/subjects': data.Resource(url_root='/courses', provider_class=data.Subject),
    '/instructors': data.Resource(url_root='/courses', provider_class=data.Instructor),
}


def root_app(environ, start_response):
    resources = {"resources": list(dispatch_appmap.keys())}
    response = Response(json.dumps(resources), mimetype='application/json')
    return response(environ, start_response)

app = DispatcherMiddleware(root_app, dispatch_appmap)
app = middleware.FieldLimiter(app)
#app = middleware.DataTransformer(app)
app = middleware.PrettyJSON(app)
