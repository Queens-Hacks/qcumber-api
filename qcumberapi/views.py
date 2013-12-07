from werkzeug.exceptions import NotImplemented
from qcumberapi.utils import expose


@expose('/')
def index(request):
    raise NotImplemented()


@expose('/subjects/', defaults={'subject_id': 'ALL'})
@expose('/subjects/<subject_id>')
def subjects(request, subject_id):
    raise NotImplemented()


@expose('/courses/', defaults={'course_id': 'ALL'})
@expose('/courses/<course_id>')
def courses(request, course_id):
    raise NotImplemented()


@expose('/sections/', defaults={'section_id': 'ALL'})
@expose('/sections/<section_id>')
def sections(request, section_id):
    raise NotImplemented()


@expose('/instructors/', defaults={'instructor_id': 'ALL'})
@expose('/instructors/<instructor_id>')
def instructors(request, instructor_id):
    raise NotImplemented()
