from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Mig001NetconnectdDisableLogDebugLevel(MigrationBaseClass):
    """
    Migration for beamos versions 0.18.0 up to 0.18.1 to disable the the netconnectd debug mode
    """

    BEAMOS_VERSION_LOW = "0.18.0"
    BEAMOS_VERSION_HIGH = "0.18.1"

    def __init__(self, plugin):
        """
        initalization of the migration 001

        Args:
            plugin: Mr Beam Plugin
        """
        super(Mig001NetconnectdDisableLogDebugLevel, self).__init__(plugin)

    @property
    def id(self):
        """
        return the id of the migration

        Returns:
            string: id of the migration
        """
        return "001"

    def _run(self):
        """
        migration steps executet during migration

        Returns:
            None
        """
        self._logger.debug("stop netconnectd service")
        self.exec_cmd("sudo service netconnectd stop")

        self._logger.debug("disable debug mode of netconnect")
        self.exec_cmd("sudo truncate -s 0 /etc/default/netconnectd")

        self._logger.debug("purge content of netconnectd.log")
        self.exec_cmd("sudo truncate -s 0 /var/log/netconnectd.log")

        self._logger.debug("restart netconnectd service")
        self.exec_cmd("sudo service netconnectd restart")

        super(Mig001NetconnectdDisableLogDebugLevel, self)._run()

    def _rollback(self):
        """
        rollback steps executet during rollback

        Returns:
            None
        """
        self._logger.debug("restart netconnectd service")
        self.exec_cmd("sudo service netconnectd restart")
        super(Mig001NetconnectdDisableLogDebugLevel, self)._rollback()
