"""
    api.data
    ~~~~~~~~

    Loads data and provides interface for it.
"""


import os
import subprocess
from api import config, ConfigException


# from subprocess import check_call, CalledProcessError


class NotEmptyRepoError(IOError):
    """Raised when an empty folder was expected, ie., for cloning."""


class DataProvider(object):
    """Reads data from the yaml files."""
    def __init__(self):
        self.RESOURCES = ['courses', 'sections', 'subjects', 'instructors']

        for attr in self.RESOURCES:
            setattr(self, attr, {})
        self.read_files()

    def read_files(self):
        # mock some data
        self.courses = {
            "ANAT100": {
                "id": "ANAT100",
                "data": "sample data for ANAT100"
            },
            "ANAT200": {
                "id": "ANAT200",
                "data": "More!!! sample data for ANAT200"
            }
        }
        pass

    def get_list(self, resource):
        if hasattr(self, resource):
            return getattr(self, resource).values()
        return None

    def get_item(self, resource, uid):
        if hasattr(self, resource):
            r_dict = getattr(self, resource)
            if uid in r_dict:
                return r_dict[uid]
        return None

data_provider = DataProvider()


def clone(force=False):
    """Pull in a fresh copy of the data repo.

    If `force` is true, then any files in the directory marked for use as the
    repo will be deleted first.
    """
    repo_dir = config['DATA_LOCAL']
    repo_uri = config['DATA_REMOTE']

    # set up the directory for the repo
    if not os.path.isdir(repo_dir):
        try:
            os.makedirs(repo_dir)
        except FileExistsError:
            raise ConfigException('The provided DATA_LOCAL directory, {}, is a file.'.format(repo_dir))
        except PermissionError:
            raise ConfigException('No write access for the provided DATA_LOCAL diretory ({}).'.format(repo_dir))

    # make sure we're workin with a fresh directory
    if len(os.listdir(repo_dir)) > 0:
        if force:
            import shutil
            shutil.rmtree(repo_dir)
        else:
            raise NotEmptyRepoError()

    # grab some data!
    subprocess.check_call(['git', 'clone', repo_uri, repo_dir])
