"""
    api.config
    ~~~~~~~~~~

    Installation-specific configuration.


    This module will load configuration from a local_config module in this
    directory if one exists, falling back on environment variables otherwise.

    A local_config module should look like this:

    `api/local_config.py`
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

    Refer to `config_variables` below as a reference for which variables you
    should set.
"""


config = {}  # importable instance of the loaded configuration
REQUIRED = object()  # used for identity checks `is REQUIRED`
message = 'Couldn\'t get "{}", {}, from {}. :('


config_variables = (
    # Variables are a three-tuple of the form (NAME, 'default' or REQUIRED, 'help text')
    ('DATA_REMOTE', 'https://github.com/Queens-Hacks/qcumber-data.git', 'the remote repository to read/write data'),
)


class ConfigException(KeyError):
    """Raised for invalid configuration"""


try:
    # If there is a local config module, use it.
    import local_config as _config_module
    _source = 'module `api.local_config`'
except ImportError:
    import os
    _config_module = None
    _source = 'environment'


for name, req, help in config_variables:
    try:
        if _config_module is None:
            config[name] = os.environ[name]
        else:
            config[name] = getattr(_config_module, name)
    except (AttributeError, KeyError):
        if req is REQUIRED:
            raise ConfigException(message.format(name, help, _source))
        else:
            config[name] = None
