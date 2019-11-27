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
    """
    option_name: str
    allowed_values: Optional[List[Any]] = field(default_factory=lambda: [True, False])
    default_value: Any = False

    def __setattr__(self, key, value):
        if key == "default_value" and value not in self.allowed_values:
            raise InvalidConfigOptionException
        else:
            super().__setattr__(key, value)


CONFIG_OPTIONS = []

CONFIG_PATH = os.path.join(os.path.abspath(__file__), '..', '..', 'config.cfg')

DEFAULT_CONFIG_PATH = os.path.join(os.path.abspath(__file__), '..', '..', 'default_config.cfg')


def get_config_options(options: List[Option], callback=False) -> Dict[str, Any]:
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
            return get_config_options(options, callback=True)
        except BackendError:
            raise
    except Exception as e:
        if config:
            config.close()
        if callback:
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
            for o in options_dict[option[0]]['allowed']:
                if str(option[1]) == str(o) and str(option[1]) != str(options_dict[option[0]]['default']):
                    return_dict[option[0]] = o
                    log.debug(f"GALAXY_CONFIG_OPTION: The option {option[0]} is now set to {str(o)} instead of "
                              f"{options_dict[option[0]]['default']}.")
                    break
        else:
            log.debug(f"GALAXY_FAKE_CONFIG_OPTION: The option {option[0]} is not a defined option!")
    config.close()
    return return_dict


class NoSuchConfigOptionException(Exception):
    pass


class InvalidConfigOptionException(Exception):
    pass
