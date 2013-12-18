"""
    api.config
    ~~~~~~~~~~

    Installation-specific configuration.


    This module will load configuration from a local_config module in the project
    directory if one exists, falling back on environment variables otherwise.

    A local_config module should look like this:

    `local_config.py`
    ```python
    CONFIG_VARIABLE = "value for this variable"
    ```

    One way to use environment variables would be to export them in a
    virtualenvwrapper postactivate hook, for example:

    `/home/$USER/.virtualenvs/qcumber-api/bin/postactivate`
    ```bash
    #!/bin/bash
    # This hook is run after this virtualenv is activated.

    export CONFIG_VARIBLE="value for this variable"
    ```

    Refer to `variables` below as a reference for which variables you should set.
"""


REQUIRED = object()  # used for identity checks `is REQUIRED`


variables = (
    # Variables are a three-tuple of the form (NAME, 'default' or REQUIRED, 'help text')
    ('DATA_REMOTE', 'https://github.com/Queens-Hacks/qcumber-data.git', 'the remote repository to read/write data'),
    ('DATA_LOCAL', 'data', 'the folder used to store the data repository locally'),
)


class ConfigException(KeyError):
    """Raised for invalid configuration"""


class _GetitemProxy(object):
    """Proxy __getitem__ access to module attributes"""

    def __init__(self, module):
        self.module = module

    def __getitem__(self, name):
        try:
            return getattr(self.module, name)
        except AttributeError as e:
            raise KeyError(e)


def get_source():
    """Try to load config by importing local_config; fall back on environment variables."""
    try:
        import local_config as config_module
        source = _GetitemProxy(config_module)
    except ImportError:
        import os
        source = os.environ
    return source


def get_config(variables, source):
    config = {}
    for name, req, help in variables:
        try:
            config[name] = source[name]
        except KeyError:
            if req is REQUIRED:
                raise ConfigException('Couldn\'t get "{}", {}. :('.format(name, help))
            else:
                config[name] = req
    return config


source = get_source()

# Create an importable instance of the loaded configuration
config = get_config(variables, source)
