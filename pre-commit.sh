#!/bin/bash

./manage.py test 2>&1 | grep "FAILED" > /dev/null
status=$?
if [ $status = 0 ]; then
    echo "unit tests failed, aborting commit"
    exit 1
fi

exit 0
