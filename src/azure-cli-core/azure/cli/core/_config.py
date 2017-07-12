# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import stat
from six.moves import configparser

from azure.cli.core._environment import get_config_dir

from knack.config import get_config_parser, CLIConfig

GLOBAL_CONFIG_DIR = get_config_dir()
CONFIG_FILE_NAME = 'config'
GLOBAL_CONFIG_PATH = os.path.join(GLOBAL_CONFIG_DIR, CONFIG_FILE_NAME)
ENV_VAR_PREFIX = 'AZURE_'
DEFAULTS_SECTION = 'defaults'

class AzCliConfig(CLIConfig):

    def set_global_config(config):
        if not os.path.isdir(GLOBAL_CONFIG_DIR):
            os.makedirs(GLOBAL_CONFIG_DIR)
        with open(GLOBAL_CONFIG_PATH, 'w') as configfile:
            config.write(configfile)
        os.chmod(GLOBAL_CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)
        # reload az_config
        az_config.config_parser.read(GLOBAL_CONFIG_PATH)


    def set_global_config_value(section, option, value):
        config = get_config_parser()
        config.read(GLOBAL_CONFIG_PATH)
        try:
            config.add_section(section)
        except configparser.DuplicateSectionError:
            pass
        config.set(section, option, value)
        set_global_config(config)
