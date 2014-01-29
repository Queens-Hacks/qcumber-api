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
import yaml


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
    repo_dir = config['DATA_LOCAL']
    repo = Repo(repo_dir)
    client = HttpGitClient(os.path.dirname(config['DATA_REMOTE']))
    remote_refs = client.fetch(os.path.basename(config['DATA_REMOTE']), repo)
    repo["HEAD"] = remote_refs["refs/heads/master"]
    indexfile = repo.index_path()
    tree = repo["HEAD"].tree
    index.build_index_from_tree(repo.path, indexfile, repo.object_store, tree)


def update_file(file_path, new_data):
    if not isinstance(new_data, dict):
        raise ValueError

    repo_dir = config['DATA_LOCAL']
    repo = Repo(repo_dir)

    abs_path = os.path.join(repo_dir, file_path)
    with open(abs_path, 'r') as infile:
        raw_data = yaml.load(infile)

    for key in new_data:
        raw_data[key] = new_data[key]

    with open(abs_path, 'w') as outfile:
        outfile.write(yaml.dump(raw_data))

    repo.stage([file_path])


def commit_changes(message=''):
    repo_dir = config['DATA_LOCAL']
    repo = Repo(repo_dir)
    c_id = repo.do_commit(message=message, committer='qcumber api <api@qcumber.ca>', ref='refs/heads/master')
    repo.refs['refs/heads/master'] = c_id
