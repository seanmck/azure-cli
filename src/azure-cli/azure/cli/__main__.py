# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

from azure.cli.core import MainCommandsLoader, AzCli
from azure.cli.core.parser import AzCliCommandParser
import azure.cli.core.telemetry as telemetry


def cli_main(cli, args):
    from azure.cli.core._session import ACCOUNT, CONFIG, SESSION

    azure_folder = cli.config.config_dir
    ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
    CONFIG.load(os.path.join(azure_folder, 'az.json'))
    SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

    return cli.invoke(args)

GLOBAL_CONFIG_DIR = os.getenv('AZURE_CONFIG_DIR', None) or os.path.expanduser(os.path.join('~', '.azure'))
ENV_VAR_PREFIX = 'AZURE_'

from azure.cli.core.application import AZ_CLI

try:
    telemetry.start()

    exit_code = cli_main(AZ_CLI, sys.argv[1:])
    
    if exit_code and exit_code != 0:
        telemetry.set_failure()
    else:
        telemetry.set_success()

    sys.exit(exit_code)
except KeyboardInterrupt:
    telemetry.set_user_fault('keyboard interrupt')
    sys.exit(1)
finally:
    telemetry.conclude()
