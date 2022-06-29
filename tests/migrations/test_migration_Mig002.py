from octoprint_mrbeam.migration.Mig002 import Mig002EnableOnlineCheck
import unittest


class TestMigrationMig002(unittest.TestCase):
    """
    Testclass for the migration Mig001
    """

    def setUp(self):
        self.m002 = Mig002EnableOnlineCheck(None)

    def test_beamos_versions(self):
        # beamos versions where the migration should not run
        self.assertFalse(self.m002.shouldrun(Mig002EnableOnlineCheck, "0.18.3"))

        # beamos versions where the migration should run
        self.assertTrue(self.m002.shouldrun(Mig002EnableOnlineCheck, "0.14.0"))
        self.assertTrue(self.m002.shouldrun(Mig002EnableOnlineCheck, "0.18.0"))
        self.assertTrue(self.m002.shouldrun(Mig002EnableOnlineCheck, "0.18.1"))
        self.assertTrue(self.m002.shouldrun(Mig002EnableOnlineCheck, "0.18.2"))

        # not matching pattern strings
        self.assertFalse(self.m002.shouldrun(Mig002EnableOnlineCheck, None))
        self.assertFalse(self.m002.shouldrun(Mig002EnableOnlineCheck, "14.0"))
        self.assertFalse(self.m002.shouldrun(Mig002EnableOnlineCheck, "0"))

    def test_migration_id(self):
        self.assertEqual(self.m002.id, "002")
