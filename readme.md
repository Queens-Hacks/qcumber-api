qcumber-api
===========

[![Build Status](https://travis-ci.org/Queens-Hacks/qcumber-api.png)](https://travis-ci.org/Queens-Hacks/qcumber-api)

Note: If you're looking for the easy to use course catalogue for Queen's University, you came close! This is the normalized filestructure database the powers it. You'll want to head over to http://qcumber.ca for the end-user site :)

Note also! Work in progress, not live yet. The current live site code is at http://github.com/ChrisCooper/QcumberD


Consumes [qcumber data](https://github.com/Queens-Hacks/qcumber-data) and denormalizes/transforms it into endpoints that are nice to work with. The [qcumber frontent](https://github.com/Queens-Hacks/qcumber-frontend) (the main public site for qcumber) consumes this api. Hopefully this api also makes it easy for anyone to make a course wiki or something that wants to hook in with the catalog.

This code will also be responsible for managing writes to qcumber-data, so managing the data can all be through this one interface.


Install
-------

qcumber-api requires python version 2.7 or 3.3. To get set up, just grab the dependancies:

```bash
$ pip install -r requirements.txt
```


Usage
-----

The `manage.py` script provides commands to do stuff. Run it with no arguments to see the full list of available commands. The two you might want:

```
$ ./manage.py runserver       # Run a local development server
$ ./manage.py test            # Run the app's test suite
```
