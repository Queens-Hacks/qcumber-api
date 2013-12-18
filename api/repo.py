"""
    api.repo
    ~~~~~~~~

    Wrap functionality for the git repo behind the filesystem db.
"""

import os
import subprocess
from api import config, ConfigException


class NotEmptyRepoError(IOError):
    """Raised when an empty folder was expected, ie., for cloning."""


def clone():
    """Pull in a fresh copy of the data repo."""
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
        raise NotEmptyRepoError()

    # grab some data!
    subprocess.check_call(['git', 'clone', repo_uri, repo_dir])
