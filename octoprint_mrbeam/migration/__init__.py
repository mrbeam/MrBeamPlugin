"""
This package contains all the migrations that are needed for the beamOS
To add a new migration create a child class of the MigrationBaseClass and extend the run and rollback method with
the steps needed for the new migration and the beamOS versions it should run for

How to use:
    - import list_of_migrations
    - iterate over the list items and run the shouldrun(<migrationclass>, <beamos_version>)
    - compare the result list with the already executed list and call the run() of the result list
"""
# these imports are for external use
from octoprint_mrbeam.migration.migration_base import MIGRATION_STATE as MIGRATION_STATE
from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass as MigrationBaseClass,
)
from octoprint_mrbeam.migration.migration_base import (
    MigrationException as MigrationException,
)
from octoprint_mrbeam.migration.migration_base import (
    MIGRATION_RESTART as MIGRATION_RESTART,
)

# this is for internal use
from octoprint_mrbeam.migration.Mig001 import Mig001NetconnectdDisableLogDebugLevel
from octoprint_mrbeam.migration.Mig002 import Mig002EnableOnlineCheck

# To add migrations they have to be added to this list till we automate it
list_of_migrations = [
    Mig001NetconnectdDisableLogDebugLevel,
    Mig002EnableOnlineCheck,
]
