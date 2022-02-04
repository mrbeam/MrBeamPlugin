from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Mig001NetconnectdDisableLogDebugLevel(MigrationBaseClass):

    BEAMOS_VERSION_LOW = "0.18.0"
    BEAMOS_VERSION_HIGH = "0.18.1"

    def __init__(self, plugin):
        super(Mig001NetconnectdDisableLogDebugLevel, self).__init__(plugin)

    @property
    def id(self):
        return "001"

    def _run(self):
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
        self._logger.debug("restart netconnectd service")
        self.exec_cmd("sudo service netconnectd restart")
        super(Mig001NetconnectdDisableLogDebugLevel, self)._rollback()
