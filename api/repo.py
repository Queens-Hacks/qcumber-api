"""
    api.repo
    ~~~~~~~~

    Wrap functionality for the git repo behind the filesystem db.
"""

import os
from api import config, ConfigException
from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from dulwich import index


class NotEmptyRepoError(IOError):
    """Raised when an empty folder was expected, ie., for cloning."""


def clone(bare=False):
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

    Repo.init_bare(repo_dir)
    pull_remote()


def pull_remote():
    repo = Repo(repo_dir)
    client = HttpGitClient(os.path.dirname(config['DATA_REMOTE']))
    remote_refs = client.fetch(os.path.basename(config['DATA_REMOTE']), repo)
    repo["HEAD"] = remote_refs["refs/heads/master"]
    indexfile = repo.index_path()
    tree = repo["HEAD"].tree
    index.build_index_from_tree(repo.path, indexfile, repo.object_store, tree)
