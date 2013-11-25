qcumber-api
===========


Note: If you're looking for the easy to use course catalogue for Queen's University, you came close! This is the normalized filestructure database the powers it. You'll want to head over to http://qcumber.ca for the end-user site :)

Note also! Work in progress, not live yet. The current live site code is at http://github.com/ChrisCooper/QcumberD


consumes [qcumber data](https://github.com/Queens-Hacks/qcumber-data) and denormalizes/transforms it into endpoints that are nice to work with. It powers the main qcumber UI, and makes it easy for anyone to make a course wiki or something that wants to hook in with the catalog.


Priorities
----------

Where the top priority for the data repo was correctness, here we're taking that correct data and making it useful.


Endpoints
---------


### Courses

Courses are identified by their three-digit (plus a letter sometimes) code, under their subject.

`GET /courses/#{subject}/` returns a list of all courses for a given subject

`GET /courses/#{subject}/#{course_code}` retrieves details about a given course

Sample course:

```YAML
name: Computer Architecture
code: 272
subject:
  name: Computer Engineering
  code: CMPE
  href: /subjects/CMPE
href: /courses/CMPE/272

... (plus a lot more stuff)
```
