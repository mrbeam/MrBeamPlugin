from octoprint_mrbeam import IS_X86
# from unittest.mock import mock_open, patch

from octoprint_mrbeam.migrate import Migration
from octoprint_mrbeam.migration import MigrationBaseClass, list_of_migrations

from octoprint_mrbeam.migration.Mig001 import Mig001NetconnectdDisableLogDebugLevel
import unittest
from octoprint_mrbeam.util.device_info import deviceInfo


class TestMigrationMig001(unittest.TestCase):
    """
    Testclass for the migration Mig001
    """
    def setUp(self):
        self.m001 = Mig001NetconnectdDisableLogDebugLevel(None)

    def test_beamos_versions(self):
        self.assertFalse(self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.14.0"))
        self.assertTrue(self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.18.0"))
        self.assertFalse(self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, "0.18.2"))
        self.assertFalse(self.m001.shouldrun(Mig001NetconnectdDisableLogDebugLevel, None))

    def test_migration_id(self):
        self.assertEqual(self.m001.id, '001')


    # def integration_test(self):
    #     deviceInfo = deviceInfo(use_dummy_values=IS_X86)
    #     beamos_version = deviceInfo.get_beamos_version_number()
    #     list_of_migrations_obj_available_to_run = [
    #         MigrationBaseClass.return_obj(migration, self.plugin)
    #         for migration in list_of_migrations
    #         if migration.shouldrun(migration, beamos_versionbeamos_version)
    #     ]
        # with patch("__builtin__.open", mock_open(read_data="0.14.0")) as mock_file:
            # mock_open.return_value = MagicMock(spec=file)
            # migration = Migration(None)
            # migration._run_migration()
            #