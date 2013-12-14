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
REQUIRED, OPTIONAL = object(), object()  # used for identity checks `is REQUIRED`
message = 'Couldn\'t get "{}", {}, from {}. :('


config_variables = (
    ('SECRET_KEY', REQUIRED, 'a long, hard-to-guess string'),
    ('DATA_REMOTE', REQUIRED, 'the remote repository to read/write data'),
)


class ConfigException(KeyError):
    """Raised for invalid configuration"""


try:
    # If there is a local config module, use it.
    import local_config as _config_module
except ImportError:
    import os
    _config_module = None


for name, req, help in config_variables:
    if _config_module is not None:
        try:
            config[name] = getattr(_config_module, name)
        except AttributeError:
            if req is REQUIRED:
                raise ConfigException(message.format(name, help, 'module `api.local_config`'))
            else:
                config[name] = None
    else:
        try:
            config[name] = os.environ[name]
        except KeyError:
            if req is REQUIRED:
                raise ConfigException(message.format(name, help, 'environment'))
            else:
                config[name] = None
