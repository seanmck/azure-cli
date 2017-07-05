# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# flake8: noqa

import os
from six.moves import configparser
import stat
import unittest
import tempfile
import mock

from azure.cli.core._config import CONFIG_FILE_NAME, set_global_config_value

from knack.config import get_config_parser


class TestSetConfig(unittest.TestCase):

    def setUp(self):
        self.config_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.config_dir, CONFIG_FILE_NAME)

    def test_set_config_value(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):
            set_global_config_value('test_section', 'test_option', 'a_value')
            config = get_config_parser()
            config.read(os.path.join(self.config_dir, CONFIG_FILE_NAME))
            self.assertEqual(config.get('test_section', 'test_option'), 'a_value')

    def test_set_config_value_duplicate_section_ok(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):
            set_global_config_value('test_section', 'test_option', 'a_value')
            set_global_config_value('test_section', 'test_option_another', 'another_value')
            config = get_config_parser()
            config.read(os.path.join(self.config_dir, CONFIG_FILE_NAME))
            self.assertEqual(config.get('test_section', 'test_option'), 'a_value')
            self.assertEqual(config.get('test_section', 'test_option_another'), 'another_value')

    def test_set_config_value_not_string(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path), \
        self.assertRaises(TypeError):
            set_global_config_value('test_section', 'test_option', False)

    def test_set_config_value_file_permissions(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):
            set_global_config_value('test_section', 'test_option', 'a_value')
            file_mode = os.stat(self.config_path).st_mode
            self.assertTrue(bool(file_mode & stat.S_IRUSR))
            self.assertTrue(bool(file_mode & stat.S_IWUSR))
            self.assertFalse(bool(file_mode & stat.S_IXUSR))
            self.assertFalse(bool(file_mode & stat.S_IRGRP))
            self.assertFalse(bool(file_mode & stat.S_IWGRP))
            self.assertFalse(bool(file_mode & stat.S_IXGRP))
            self.assertFalse(bool(file_mode & stat.S_IROTH))
            self.assertFalse(bool(file_mode & stat.S_IWOTH))
            self.assertFalse(bool(file_mode & stat.S_IXOTH))


if __name__ == '__main__':
    unittest.main()
