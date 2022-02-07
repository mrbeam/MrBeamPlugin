"""
what it is
what it does
suggestion how to use
    example
"""
# these imports are for external use
from octoprint_mrbeam.migration.migration_base import MIGRATION_STATE as MIGRATION_STATE
from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass as MigrationBaseClass,
)
from octoprint_mrbeam.migration.migration_base import (
    MigrationException as MigrationException,
)

# this is for internal use
from octoprint_mrbeam.migration.Mig001 import Mig001NetconnectdDisableLogDebugLevel

# To add migrations they have to be added to this list till we automate it
list_of_migrations = [
    Mig001NetconnectdDisableLogDebugLevel,
]
