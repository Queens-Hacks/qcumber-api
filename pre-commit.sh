#!/bin/bash

FILES=$(git diff --cached --name-status | grep -v ^D | awk '$1 $2 { print $2}' | grep -e .py)
if [ -n "$FILES" ]; then
    pep8 -r --max-line-length=119 $FILES
    status=$?
    if [ $status != 0 ]; then
        echo "pep8 check failed, aborting commit"
        exit 1
    fi
fi

./manage.py test 2>&1 | grep "FAILED" > /dev/null
status=$?
if [ $status = 0 ]; then
    echo "unit tests failed, aborting commit"
    exit 1
fi

exit 0
