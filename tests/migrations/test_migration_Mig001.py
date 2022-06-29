from octoprint_mrbeam.migration.Mig001 import Mig001NetconnectdDisableLogDebugLevel
import unittest


class TestMigrationMig001(unittest.TestCase):
    """
    Testclass for the migration Mig001
    """

    def setUp(self):
        self.m001 = Mig001NetconnectdDisableLogDebugLevel(None)

    def test_beamos_versions(self):
        # beamos versions where the migration should not run
        self.assertFalse(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.14.0")
        )
        self.assertFalse(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.18.2")
        )

        # beamos versions where the migration should run
        self.assertTrue(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.18.0")
        )
        self.assertTrue(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.18.1")
        )

        # not matching pattern strings
        self.assertFalse(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, None)
        )
        self.assertFalse(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "14.0")
        )
        self.assertFalse(
            self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0")
        )

    def test_migration_id(self):
        self.assertEqual(self.m001.id, "001")
