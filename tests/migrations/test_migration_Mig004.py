import os

from mock import patch

from octoprint_mrbeam.migration import Mig004DisableDebugLogging
import unittest


class TestMigrationMig004(unittest.TestCase):
    """Testclass for the migration Mig001."""

    def setUp(self):
        self.m004 = Mig004DisableDebugLogging(None)

    def test_beamos_versions(self):
        # beamos versions where the migration should not run
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, "0.19.0"))
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, "0.18.0"))
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, "0.18.1"))
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, "0.18.2"))

        # beamos versions where the migration should run
        self.assertTrue(self.m004.shouldrun(Mig004DisableDebugLogging, "0.14.0"))

        # not matching pattern strings
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, None))
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, "14.0"))
        self.assertFalse(self.m004.shouldrun(Mig004DisableDebugLogging, "0"))

    def test_migration_id(self):
        self.assertEqual(self.m004.id, "004")

    @patch.object(
        Mig004DisableDebugLogging,
        "exec_cmd",
    )
    def test_commands_executed(self, exec_cmd_mock):
        self.m004.run()
        exec_cmd_mock.assert_any_call(
            "sudo rm /home/pi/.octoprint/logging.yaml", optional=True
        )
