qcumber-api
===========

[![Build Status](https://travis-ci.org/Queens-Hacks/qcumber-api.png)](https://travis-ci.org/Queens-Hacks/qcumber-api)

Note: If you're looking for the easy to use course catalogue for Queen's University, you came close! This is the normalized filestructure database the powers it. You'll want to head over to http://qcumber.ca for the end-user site :)

Note also! Work in progress, not live yet. The current live site code is at http://github.com/ChrisCooper/QcumberD


Consumes [qcumber data](https://github.com/Queens-Hacks/qcumber-data) and denormalizes/transforms it into endpoints that are nice to work with. The [qcumber frontend](https://github.com/Queens-Hacks/qcumber-frontend) (the main public site for qcumber) consumes this api. Hopefully this api also makes it easy for anyone to make a course wiki or something that wants to hook in with the catalog.

This code will also be responsible for managing writes to qcumber-data, so managing the data can all be through this one interface.


Install
-------


### 1. Python & Git

Python 2.7 or 3.3 and git must be installed on your system to run qcumber-api.

To get set up, just grab the dependancies:


### 2. Application Requirements

You'll probably want to use a [virtualenv](http://www.virtualenv.org/en/latest/), maybe with [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/).

```bash
(venv) $ pip install -r requirements.txt
```

### 3. Tests & Formatting

You'll also need to set up a precommit hook for `pep8` to keep with the style spec:


```bash
$ ln -s ../../pre-commit.sh .git/hooks/pre-commit
```

### 4. Local Configuration

A couple variables can be set locally. You can either create the file `api/local_config.py` and define the variables there, or export them to your environment. An example `local_config`:

```python
DATA_REMOTE = https://github.com/Queens-Hacks/qcumber-data.git
```

At the moment, there are no required config variables. The definitive list of config variables can be found [in the config module](api/config.py#L36) on line 36.


### 5. Get Data

Run `init` to grab data from the repo. The exact repo to pull from is set by your config, and it defaults to https://github.com/Queens-Hacks/qcumber-data.git.

```bash
(venv) $ ./manage.py init
```


Usage
-----

The `manage.py` script provides commands to do stuff. Run it with no arguments to see the full list of available commands. The two you might want:

```
$ ./manage.py runserver       # Run a local development server
$ ./manage.py test            # Run the app's test suite
```
