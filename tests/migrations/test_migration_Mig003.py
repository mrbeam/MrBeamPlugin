import os

from mock import patch

from octoprint_mrbeam.migration import Mig003EnableLogrotateBuster
import unittest


class TestMigrationMig003(unittest.TestCase):
    """
    Testclass for the migration Mig001
    """

    def setUp(self):
        self.m003 = Mig003EnableLogrotateBuster(None)

    def test_beamos_versions(self):
        # beamos versions where the migration should not run
        self.assertFalse(self.m003.shouldrun(Mig003EnableLogrotateBuster, "0.19.0"))

        # beamos versions where the migration should run
        self.assertTrue(self.m003.shouldrun(Mig003EnableLogrotateBuster, "0.14.0"))
        self.assertTrue(self.m003.shouldrun(Mig003EnableLogrotateBuster, "0.18.0"))
        self.assertTrue(self.m003.shouldrun(Mig003EnableLogrotateBuster, "0.18.1"))
        self.assertTrue(self.m003.shouldrun(Mig003EnableLogrotateBuster, "0.18.2"))

        # not matching pattern strings
        self.assertFalse(self.m003.shouldrun(Mig003EnableLogrotateBuster, None))
        self.assertFalse(self.m003.shouldrun(Mig003EnableLogrotateBuster, "14.0"))
        self.assertFalse(self.m003.shouldrun(Mig003EnableLogrotateBuster, "0"))

    def test_migration_id(self):
        self.assertEqual(self.m003.id, "003")

    @patch.object(
        Mig003EnableLogrotateBuster,
        "exec_cmd",
    )
    def test_commands_executed(self, exec_cmd_mock):
        self.m003.run()
        exec_cmd_mock.assert_any_call(
            "sudo rm /etc/logrotate.d/iobeam.logrotate", optional=True
        )
        logrotates = [
            "analytics",
            "iobeam",
            "mount_manager",
            "mrb_check",
            "mrbeam_ledstrips",
            "netconnectd",
        ]
        for logrotate in logrotates:
            dst = os.path.join("/etc/logrotate.d/" + logrotate)
            src = os.path.join(
                __package_path__,
                "files/migrate_logrotate",
                logrotate,
            )
            exec_cmd_mock.assert_any_call(
                "sudo cp {src} {dst}".format(src=src, dst=dst)
            )

        exec_cmd_mock.ssert_any_call("sudo logrotate /etc/logrotate.conf")
