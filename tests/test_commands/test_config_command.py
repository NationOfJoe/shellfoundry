#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from click import BadArgumentUsage
from mock import patch, call, Mock
from pyfakefs import fake_filesystem_unittest

from shellfoundry.commands.config_command import ConfigCommandExecutor


class TestConfigCommandExecutor(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_get_all_config_keys(self, echo_mock, get_app_dir_mock):
        # Arrange
        self.fs.CreateFile('/quali/shellfoundry/global_config.yml', contents="""
install:
  key: value
not_supported_section:
  no_key: no_value
    """)
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        # Act
        ConfigCommandExecutor(True).config()

        # Assert
        output = echo_mock.mock_calls[0][1][0]
        self.assertRegexpMatches(output, 'key.+value')
        self.assertRegexpMatches(output, 'online_mode.+True')
        self.assertRegexpMatches(output, 'password.+[encrypted]')
        self.assertRegexpMatches(output, 'template_location.+Empty')
        self.assertRegexpMatches(output, 'port.+9000')
        self.assertRegexpMatches(output, 'domain.+Global')
        self.assertRegexpMatches(output, 'username.+admin')
        self.assertRegexpMatches(output, 'defaultview.+gen2')
        self.assertNotRegexpMatches(output, 'no_key.+no_value')

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_set_global_config_key(self, echo_mock, get_app_dir_mock):
        # Arrange
        self.fs.CreateFile('/quali/shellfoundry/global_config.yml', contents="""
install:
  key: value""")
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        # Act
        ConfigCommandExecutor(True).config(('new_key', 'new_value'))

        # Assert
        echo_mock.assert_called_once_with('new_key: new_value was saved successfully')
        desired_result = """install:
  key: value
  new_key: new_value
"""
        self.assertTrue(self.fs.GetObject('/quali/shellfoundry/global_config.yml').contents == desired_result)

    @patch('shellfoundry.utilities.config.config_providers.os.getcwd')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_set_local_config_key(self, echo_mock, getcwd_mock):
        # Arrange
        self.fs.CreateFile('/current_shell/cloudshell_config.yml', contents="""
install:
  key: value""")
        getcwd_mock.return_value = '/current_shell'
        # Act
        ConfigCommandExecutor(False).config(('new_key', 'new_value'))

        # Assert
        echo_mock.assert_called_with('new_key: new_value was saved successfully')
        desired_result = """install:
  key: value
  new_key: new_value
"""
        self.assertTrue(self.fs.GetObject('/current_shell/cloudshell_config.yml').contents == desired_result)

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_get_all_config_keys_that_has_password_param(self, echo_mock, get_app_dir_mock):
        # Arrange
        self.fs.CreateFile('/quali/shellfoundry/global_config.yml', contents="""
install:
  key: value
  password: aabcdefs
  yetanotherkey: yetanothervalue""")
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        # Act
        ConfigCommandExecutor(True).config()

        # Assert
        output = echo_mock.mock_calls[0][1][0]
        self.assertRegexpMatches(output, 'key.+value')
        self.assertRegexpMatches(output, 'yetanotherkey.+yetanothervalue')
        self.assertRegexpMatches(output, 'password.+[encrypted]')

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_remove_key_is_allowed(self, echo_mock, get_app_dir_mock):
        # Arrange
        self.fs.CreateFile('/quali/shellfoundry/global_config.yml', contents="""
install:
  key: value
  yetanotherkey: yetanothervalue""")
        get_app_dir_mock.return_value = '/quali/shellfoundry'
        key = 'yetanotherkey'

        # Act
        ConfigCommandExecutor(True).config(key_to_remove=key)

        # Assert
        echo_mock.assert_called_once_with('yetanotherkey was deleted successfully')
        desired_result = """install:
  key: value
"""
        file_content = self.fs.GetObject('/quali/shellfoundry/global_config.yml').contents
        self.assertTrue(file_content == desired_result, 'Expected: {}{}Actual: {}'
                        .format(desired_result, os.linesep, file_content))

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_remove_key_from_global_where_global_config_file_does_not_exists(self, echo_mock, get_app_dir_mock):
        # Arrange
        get_app_dir_mock.return_value = '/quali/shellfoundry'
        key = 'yetanotherkey'

        # Act
        ConfigCommandExecutor(True).config(key_to_remove=key)

        # Assert
        echo_mock.assert_called_with('Failed to delete key')

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_update_existing_key(self, echo_mock, get_app_dir_mock):
        # Arrange
        self.fs.CreateFile('/quali/shellfoundry/global_config.yml', contents="""
install:
  key: value""")
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        # Act
        ConfigCommandExecutor(True).config(('key', 'new_value'))

        # Assert
        echo_mock.assert_called_once_with('key: new_value was saved successfully')
        desired_result = """install:
  key: new_value
"""
        file_content = self.fs.GetObject('/quali/shellfoundry/global_config.yml').contents
        self.assertTrue(file_content == desired_result, 'Expected: {}{}Actual: {}'
                        .format(desired_result, os.linesep, file_content))

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_adding_key_to_global_config_that_hasnt_been_created_yet(self, echo_mock, get_app_dir_mock):
        # Arrange
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        # Act
        ConfigCommandExecutor(True).config(('key', 'new_value'))

        # Assert
        echo_mock.assert_called_with('key: new_value was saved successfully')
        desired_result = """install:
  key: new_value
"""
        file_content = self.fs.GetObject('/quali/shellfoundry/global_config.yml').contents
        self.assertTrue(file_content == desired_result, 'Expected: {}{}Actual: {}'
                        .format(desired_result, os.linesep, file_content))

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('shellfoundry.commands.config_command.click.echo')
    def test_adding_key_to_global_config_with_empty_value(self, echo_mock, get_app_dir_mock):
        # Arrange
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        with self.assertRaisesRegexp(BadArgumentUsage, "Field '.+' cannot be empty"):
            ConfigCommandExecutor(True).config(('key', ''))

    @patch('shellfoundry.utilities.config.config_providers.click.get_app_dir')
    @patch('platform.node', Mock(return_value='machine-name-here'))
    def test_set_password_config_password_should_appear_encrypted(self, get_app_dir_mock):
        # Arrange
        self.fs.CreateFile('/quali/shellfoundry/global_config.yml', contents="""
install:
  key: value
""")
        get_app_dir_mock.return_value = '/quali/shellfoundry'

        # Act
        ConfigCommandExecutor(True).config(('password', 'admin'))

        # Assert
        desired_result = """install:
  key: value
  password: DAUOAQc=
"""
        file_content = self.fs.GetObject('/quali/shellfoundry/global_config.yml').contents
        self.assertTrue(file_content == desired_result, 'Expected: {}{}Actual: {}'
                        .format(desired_result, os.linesep, file_content))
