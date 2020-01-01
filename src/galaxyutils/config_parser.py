from dataclasses import dataclass, field
from galaxy.api.errors import BackendError
from typing import Dict, Any, List, Optional

import logging as log
import os


@dataclass
class Option(object):
    """
    Create a new ``Option`` object to define a customizable option. The ``option_name`` value must be the same value as
    is provided within the plugin's ``default_config.cfg`` file.

    :param option_name: The name of the option which will be configured. This name must match the name provided within
        the plugin's ``default_config.cfg`` file.
    :param str_option: This defines whether or not the option uses ``str`` values. It allows any values to be used, so
        long as it is an ``str`` value. If this parameter is not defined, then the default value of ``False`` is used.
    :param allowed_values: This defines the list of possible values that the option can take. If this parameter is not
        defined, then the default list of ``[True, False]`` is used.
    :param default_value: This defines the default value of the option. This value is used if the specified option
        cannot be found in the generated ``config.cfg`` file, or if the value assigned to the option within this file is
        not in the ``allowed_values`` list. If this parameter is not defined, then the default value of ``False`` is
        used.
    :raises InvalidConfigOptionException: This exception is thrown if the ``Option`` object is created with a
        ``default_value`` value that is not in the ``allowed_values`` list.

    """
    option_name: str
    str_option: Optional[bool] = False
    allowed_values: Optional[List[Any]] = field(default_factory=lambda: [True, False])
    default_value: Optional[Any] = False

    def __setattr__(self, key, value):
        if key == "default_value":
            if self.str_option or value in self.allowed_values:
                super().__setattr__("default_value", value)
            else:
                log.debug(f"Name: {self.option_name} / str_option: {str(self.str_option)} / "
                          f"allowed_values: {str(self.allowed_values)} / default_value: {self.default_value}")
                raise InvalidConfigOptionException
        else:
            super().__setattr__(key, value)


CONFIG_OPTIONS = []

CONFIG_PATH = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', 'config.cfg'))

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', 'default_config.cfg'))


def get_config_options(options: List[Option]) -> Dict[str, Any]:
    """
    Using a specified list of ``Option`` objects (``options``), this method returns a dictionary consisting of the
    various options names as keys and their respective value as values. The returned option values are either the values
    specified according to the ``config.cfg`` file or, if the value in the ``config.cfg`` file is not in the option's
    list of allowed values, the default values. If a ``config.cfg`` file is not present in the root of the plugin
    directory, then it is created as a copy of ``default_config.cfg``.

    :param options: The list of ``Option`` objects which will have their value returned.
    :raises FileNotFoundError: This exception is raised if the ``default_config.cfg`` file is not contained within the
        root of the plugin directory.
    :raises galaxy.api.errors.BackendError: This exception is raised for a variety of failures regarding reading and
        creating the ``config.cfg`` file and reading the ``default_config.cfg`` file. The underlying exception is
        contained within an entry written to the plugin's log file. Please report any occurrences of this error on the
        module repository on GitHub.

    Example:
        .. code-block:: python

            # Set the valid options for later use here.
            CONFIG_OPTIONS = get_config_options([
                Option(option_name="log_sensitive_data"),
                Option(option_name="user_presence_mode", default_value=1, allowed_values=[i for i in range(0, 4)])
            ])

            # After get_config_options() has been called, the user's configuration options can be used.
            LOG_SENSITIVE_DATA = CONFIG_OPTIONS['log_sensitive_data']  # This will be False, unless
                                                                       # log_sensitive_data=True is in config.cfg.

    """
    return _get_config_options(options, False)


def _get_config_options(options: List[Option], _callback=False) -> Dict[str, Any]:
    global CONFIG_OPTIONS
    CONFIG_OPTIONS = options
    config = None
    try:
        config = open(CONFIG_PATH, "r")
        options = _parse_config(config)
        config.close()
        return options
    except FileNotFoundError:
        log.warning("GALAXY_CONFIG_MISSING: The config.cfg file could not be found in the root of the directory!")
        try:
            _copy_default_config()
        except FileNotFoundError:
            log.error("GALAXY_DEFAULT_CONFIG_MISSING: The default_config.cfg file could not be found in the root "
                      "of the directory! Closing the plugin...")
            raise BackendError
        except Exception as e:
            log.exception("GALAXY_DEFAULT_COPY_ERROR: Attempting to copy the default_config.cfg file to a new "
                          f"config.cfg resulted in this exception: {repr(e)}.")
            raise BackendError
        try:
            return _get_config_options(options, _callback=True)
        except BackendError:
            raise
    except Exception as e:
        if config:
            config.close()
        if _callback:
            log.exception(f"GALAXY_READ_CONFIG_CALLBACK_ERROR: Attempting to read the config.cfg file resulted in"
                          f" the exception {repr(e)} even after the default_config.cfg file was replicated. Closing"
                          f" the plugin...")
        else:
            log.exception(f"GALAXY_READ_CONFIG_ERROR: The exception {repr(e)} was thrown while attempting to read"
                          f" the existing config.cfg file.")
        raise BackendError


def _copy_default_config() -> None:
    default_config = open(DEFAULT_CONFIG_PATH, 'r')
    config = open(CONFIG_PATH, 'w+')
    escaped_default_strings = False
    for line in default_config:
        if not escaped_default_strings:
            if line[:2] == "##":
                continue
            if line not in ['\r\n', '\n']:
                config.write(line)
                escaped_default_strings = True
        else:
            if line[:2] == "##":
                escaped_default_strings = False
                continue
            config.write(line)
    default_config.close()
    config.close()


def _parse_config(config) -> Dict[str, Any]:
    options_dict = {}
    return_dict = {}
    for op in CONFIG_OPTIONS:
        options_dict[op.option_name] = {
            'str_option': op.str_option,
            'default': op.default_value,
            'allowed': op.allowed_values
        }
        return_dict[op.option_name] = op.default_value
    for line in config:
        if line[:1] == "#" or line in ['\r\n', '\n']:
            continue
        option = line.split("=")
        option[0] = option[0].strip()  # Remove possible spaces before/after the option name.
        option[1] = option[1].strip()  # Remove possible spaces before/after the option value.
        if option[0] in options_dict:
            if options_dict[option[0]]['str_option'] and option[1] != "None":
                return_dict[option[0]] = option[1]
                log.debug(f"GALAXY_CONFIG_OPTION: The option {option[0]} is now set to {option[1]}.")
            else:
                for o in options_dict[option[0]]['allowed']:
                    if str(option[1]).lower() == str(o).lower() and str(option[1]) != \
                            str(options_dict[option[0]]['default']):
                        return_dict[option[0]] = o
                        log.debug(f"GALAXY_CONFIG_OPTION: The option {option[0]} is now set to {str(o)} instead of "
                                  f"{options_dict[option[0]]['default']}.")
                        break
        else:
            log.debug(f"GALAXY_FAKE_CONFIG_OPTION: The option {option[0]} is not a defined option!")
    config.close()
    return return_dict


class InvalidConfigOptionException(Exception):
    pass
