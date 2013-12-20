#!/bin/bash

# unit tests fail with a zero exit status but say 'FAILED'
# other things in the manage.py test may fail, so have to also test for non-zero exit
./manage.py test 2>&1 | grep "FAILED" > /dev/null

status=( ${PIPESTATUS[@]} )

if  [ ${status[0]} -ne 0 ] || [ ${status[1]} -ne 1 ] ; then
    echo "unit tests failed, aborting commit"
    exit 1
fi

exit 0
