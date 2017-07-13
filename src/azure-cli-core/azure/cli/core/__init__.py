# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

__version__ = "2.0.11+dev"

import os

from knack.cli import CLI
from knack.commands import CLICommandsLoader, CLICommand
from knack.completion import ARGCOMPLETE_ENV_NAME
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.log import get_logger
import six

logger = get_logger(__name__)

class AzCli(CLI):

    def __init__(self, **kwargs):
        super(AzCli, self).__init__(**kwargs)
        self.data['headers'] = {}  # the x-ms-client-request-id is generated before a command is to execute
        self.data['command'] = 'unknown'
        self.data['completer_active'] = ARGCOMPLETE_ENV_NAME in os.environ
        self.data['query_active'] = False

    def get_cli_version(cli):
        from azure.cli.core.util import get_az_version_string
        return get_az_version_string(cli.output)


class AzCliCommand(CLICommand):

    def _resolve_default_value_from_cfg_file(self, arg, overrides):
        from azure.cli.core._config import DEFAULTS_SECTION

        if not hasattr(arg.type, 'required_tooling'):
            required = arg.type.settings.get('required', False)
            setattr(arg.type, 'required_tooling', required)
        if 'configured_default' in overrides.settings:
            def_config = overrides.settings.pop('configured_default', None)
            setattr(arg.type, 'default_name_tooling', def_config)
            # same blunt mechanism like we handled id-parts, for create command, no name default
            if (self.name.split()[-1] == 'create' and overrides.settings.get('metavar', None) == 'NAME'):
                return
            setattr(arg.type, 'configured_default_applied', True)
            config_value = self.ctx.config.get(DEFAULTS_SECTION, def_config, None)
            if config_value:
                logger.warning("Using default '%s' for arg %s", config_value, arg.name)
                overrides.settings['default'] = config_value
                overrides.settings['required'] = False

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        self._resolve_default_value_from_cfg_file(arg, argtype)
        arg.type.update(other=argtype)


class MainCommandsLoader(CLICommandsLoader):

    def __init__(self, ctx=None):
        super(MainCommandsLoader, self).__init__(ctx)
        self.loaders = []

    def load_command_table(self, args):
        from azure.cli.core.commands import get_command_table
        self.command_table = get_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.core.commands.parameters import resource_group_name_type, location_type, deployment_name_type

        for loader in self.loaders:
            loader.load_arguments(command)
            self.argument_registry.arguments.update(loader.argument_registry.arguments)

        self.register_cli_argument('', 'resource_group_name', resource_group_name_type)
        self.register_cli_argument('', 'location', location_type)
        self.register_cli_argument('', 'deployment_name', deployment_name_type)
        super(MainCommandsLoader, self).load_arguments(command)


class AzCommandsLoader(CLICommandsLoader):

    def __init__(self, ctx=None):
        super(AzCommandsLoader, self).__init__(ctx=ctx)
        self.command_module_map = {}

    def cli_generic_update_command(self, *args, **kwargs):
        from azure.cli.core.commands.arm import cli_generic_update_command as command
        return command(self, *args, **kwargs)

    def cli_generic_wait_command(self, *args, **kwargs):
        from azure.cli.core.commands.arm import cli_generic_wait_command as command
        return command(self, *args, **kwargs)

    # TODO: should not have to duplicate this logic just to use a derived CLICommand class
    def create_command(self, module_name, name, operation, **kwargs):  # pylint: disable=unused-argument
        if not isinstance(operation, six.string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        name = ' '.join(name.split())

        confirmation = kwargs.get('confirmation', False)
        client_factory = kwargs.get('client_factory', None)

        def _command_handler(command_args):
            if confirmation \
                and not command_args.get('_confirm_yes') \
                and not self.ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False) \
                    and not CLICommandsLoader.user_confirmed(confirmation, command_args):
                self.ctx.raise_event(EVENT_COMMAND_CANCELLED, command=name, command_args=command_args)
                raise CLIError('Operation cancelled.')
            op = CLICommandsLoader.get_op_handler(operation)
            client = client_factory(command_args) if client_factory else None
            result = op(client, **command_args) if client else op(**command_args)
            return result

        def arguments_loader():
            return extract_args_from_signature(CLICommandsLoader.get_op_handler(operation))

        def description_loader():
            return extract_full_summary_from_signature(CLICommandsLoader.get_op_handler(operation))

        kwargs['arguments_loader'] = arguments_loader
        kwargs['description_loader'] = description_loader

        cmd = AzCliCommand(self.ctx, name, _command_handler, **kwargs)
        if confirmation:
            cmd.add_argument('yes', '--yes', '-y', dest='_confirm_yes', action='store_true',
                             help='Do not prompt for confirmation')
        return cmd

