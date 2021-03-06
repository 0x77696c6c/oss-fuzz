# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
"""Unit tests for Cloud Function request builds which builds projects."""
import json
import datetime
import os
import unittest
from unittest import mock

from google.cloud import ndb

from datastore_entities import Project
from request_build import get_build_steps
import test_utils


class TestRequestBuilds(unittest.TestCase):
  """Unit tests for sync."""

  @classmethod
  def setUpClass(cls):
    cls.ds_emulator = test_utils.start_datastore_emulator()
    test_utils.wait_for_emulator_ready(cls.ds_emulator, 'datastore',
                                       test_utils.DATASTORE_READY_INDICATOR)
    test_utils.set_gcp_environment()

  def setUp(self):
    test_utils.reset_ds_emulator()

  @mock.patch('build_lib.get_signed_url', return_value='test_url')
  @mock.patch('datetime.datetime')
  def test_get_build_steps(self, mocked_url, mocked_time):
    """Test for get_build_steps."""
    del mocked_url, mocked_time
    datetime.datetime = test_utils.SpoofedDatetime
    project_yaml_contents = ('language: c++\n'
                             'sanitizers:\n'
                             '  - address\n'
                             'architectures:\n'
                             '  - x86_64\n')
    image_project = 'oss-fuzz'
    base_images_project = 'oss-fuzz-base'
    testcase_path = os.path.join(os.path.dirname(__file__),
                                 'expected_build_steps.json')
    with open(testcase_path) as testcase_file:
      expected_build_steps = json.load(testcase_file)

    with ndb.Client().context():
      Project(name='test-project',
              project_yaml_contents=project_yaml_contents,
              dockerfile_contents='test line').put()

    build_steps = get_build_steps('test-project', image_project,
                                  base_images_project)
    self.assertEqual(build_steps, expected_build_steps)

  def test_get_build_steps_no_project(self):
    """Test for when project isn't available in datastore."""
    with ndb.Client().context():
      self.assertRaises(RuntimeError, get_build_steps, 'test-project',
                        'oss-fuzz', 'oss-fuzz-base')

  @classmethod
  def tearDownClass(cls):
    test_utils.cleanup_emulator(cls.ds_emulator)


if __name__ == '__main__':
  unittest.main(exit=False)
