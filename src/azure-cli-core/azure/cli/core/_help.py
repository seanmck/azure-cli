# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys

from knack.help import \
    (HelpExample, CommandHelpFile, GroupHelpFile, HelpFile as KnackHelpFile,
     ArgumentGroupRegistry as KnackArgumentGroupRegistry, print_description_list, _print_indent,
     print_detailed_help)


__all__ = ['print_detailed_help', 'print_welcome_message', 'GroupHelpFile', 'CommandHelpFile']


PRIVACY_STATEMENT = """
Welcome to Azure CLI!
---------------------
Use `az -h` to see available commands or go to https://aka.ms/cli.

Telemetry
---------
The Azure CLI collects usage data in order to improve your experience.
The data is anonymous and does not include commandline argument values.
The data is collected by Microsoft.

You can change your telemetry settings with `az configure`.
"""


def show_privacy_statement():
    first_ran = az_config.getboolean('core', 'first_run', fallback=False)
    if not first_ran:
        print(PRIVACY_STATEMENT, file=sys.stdout)
        set_global_config_value('core', 'first_run', 'yes')


def show_help(nouns, parser, is_group):
    delimiters = ' '.join(nouns)
    help_file = CommandHelpFile(delimiters, parser) \
        if not is_group \
        else GroupHelpFile(delimiters, parser)

    help_file.load(parser)

    if not nouns:
        print("\nFor version info, use 'az --version'")
        help_file.command = ''

    print_detailed_help('az', help_file)


def show_welcome(parser):
    show_privacy_statement()
    print_welcome_message()

    help_file = GroupHelpFile('', parser)
    print_description_list(help_file.children)


def print_welcome_message():
    _print_indent(r"""
     /\
    /  \    _____   _ _ __ ___
   / /\ \  |_  / | | | \'__/ _ \
  / ____ \  / /| |_| | | |  __/
 /_/    \_\/___|\__,_|_|  \___|
""")
    _print_indent('\nWelcome to the cool new Azure CLI!\n\nHere are the base commands:\n')


class ArgumentGroupRegistry(KnackArgumentGroupRegistry):  # pylint: disable=too-few-public-methods

    def __init__(self, group_list):

        super(ArgumentGroupRegistry, self).__init__()
        self.priorities = {
            None: 0,
            'Resource Id Arguments': 1,
            'Generic Update Arguments': 998,
            'Global Arguments': 1000,
        }
        priority = 2
        # any groups not already in the static dictionary should be prioritized alphabetically
        other_groups = [g for g in sorted(list(set(group_list))) if g not in self.priorities]
        for group in other_groups:
            self.priorities[group] = priority
            priority += 1


class HelpFile(KnackHelpFile):  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    @staticmethod
    def _should_include_example(ex):
        min_profile = ex.get('min_profile')
        max_profile = ex.get('max_profile')
        if min_profile or max_profile:
            from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
            # yaml will load this as a datetime if it's a date, we need a string.
            min_profile = str(min_profile) if min_profile else None
            max_profile = str(max_profile) if max_profile else None
            return supported_api_version(PROFILE_TYPE,
                                         min_api=min_profile,
                                         max_api=max_profile)
        return True

    def _load_from_data(self, data):
        if not data:
            return

        if isinstance(data, str):
            self.long_summary = data
            return

        if 'type' in data:
            self.type = data['type']

        if 'short-summary' in data:
            self.short_summary = data['short-summary']

        self.long_summary = data.get('long-summary')

        if 'examples' in data:
            self.examples = []
            for d in data['examples']:
                if HelpFile._should_include_example(d):
                    self.examples.append(HelpExample(d))
