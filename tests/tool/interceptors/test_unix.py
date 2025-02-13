from sys import platform
import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import tempfile
import shutil

from datetime import datetime, timezone

import pytest

from safety.tool.interceptors.unix import UnixAliasInterceptor


@pytest.mark.unix_only
@pytest.mark.skipif(platform not in ["linux", "linux2", "darwin"], 
                    reason="Unix-specific tests")
class TestUnixAliasInterceptor(unittest.TestCase):

    def setUp(self):        
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    @patch('safety.tool.interceptors.unix.Path.home')
    @patch('safety.tool.interceptors.base.datetime')
    @patch('safety.tool.interceptors.base.get_version')    
    def test_interceptors_all_tools(self, mock_version,
                                            mock_datetime,
                                            mock_home):

        mock_home.return_value = Path(self.temp_dir)
        mock_version.return_value = "1.0.0"
        mock_now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        safety_config_user_dir = Path(self.temp_dir) / '.safety'

        with patch('safety.tool.interceptors.unix.USER_CONFIG_DIR', 
                   safety_config_user_dir):            

          interceptor = UnixAliasInterceptor()
          result = interceptor.install_interceptors()

          self.assertTrue(result)
          
          profile_path = Path(self.temp_dir) / '.profile'
          safety_profile_path = Path(self.temp_dir) / '.safety' / '.safety_profile'
          
          self.assertTrue(profile_path.exists())
          self.assertTrue(safety_profile_path.exists())
          
          # test the content of the generated files
          expected_profile_content = (
              "# >>> Safety >>>\n"
              f'[ -f "{safety_profile_path}" ] && . "{safety_profile_path}"\n'
              "# <<< Safety <<<\n"
          )
          
          expected_safety_profile_content = (
              "# >>> Safety >>>\n"
              "# DO NOT EDIT THIS FILE DIRECTLY\n"
              f"# Last updated at: {mock_now.isoformat()}\n"
              "# Updated by: safety v1.0.0\n"
              'alias pip="safety pip"\n'
              'alias pip3="safety pip"\n'
              "# <<< Safety <<<\n"
          )
          
          self.assertEqual(profile_path.read_text(), expected_profile_content)
          self.assertEqual(safety_profile_path.read_text(),
                          expected_safety_profile_content)
          
          # Let's test remove_interceptors
          result = interceptor.remove_interceptors()
          
          self.assertTrue(result)          
          self.assertTrue(profile_path.exists())
          self.assertEqual(profile_path.read_text(), "")

          self.assertFalse(safety_profile_path.exists())          

    def test_install_interceptors_nonexistent_tool(self):        
        interceptor = UnixAliasInterceptor()
        result = interceptor.install_interceptors(['nonexistent'])
        self.assertFalse(result)

    def test_uninstall_interceptors_all_tools(self):
        interceptor = UnixAliasInterceptor()
        result = interceptor.install_interceptors()
        self.assertTrue(result)
