# TODO Baseclass
import abc, six
from abc import abstractmethod

from octoprint_mrbeam import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd

MIGRATE_NETCONNECTD = "0.10.1-hotfix"


class MIGRATION_STATE(enumerate):
    init = 1
    migrate = 2
    migrationDone = 3
    rollback = 4
    rollbackDone = 5
    error = -1


@six.add_metaclass(abc.ABCMeta)
class MigrationBaseClass:
    MIGRATE_FILES_FOLDER = "files/migrate/"

    def __init__(self, plugin, version):
        self.plugin = plugin
        self.version = version
        self.state = MIGRATION_STATE.init
        self._logger = mrb_logger(
            "octoprint.plugins.mrbeam.migrate." + self.__class__.__name__
        )
        beamos_tier, self.beamos_date = self.plugin._device_info.get_beamos_version()

    @abc.abstractmethod
    @abstractmethod
    def _run(self):
        pass

    @abstractmethod
    def _rollback(self):
        pass

    def run(self):
        self._setState(MIGRATION_STATE.migrate)
        self._logger.info("start migration of " + self.__class__.__name__)
        try:
            self._run()
            self._setState(MIGRATION_STATE.migrationDone)
            self._logger.info("end migration of " + self.__class__.__name__)
            if self.state != MIGRATION_STATE.migrationDone:
                self.rollback()
        except Exception as e:
            self._logger.exception("exception during migration: {}".format(e))
            self.rollback()

    def rollback(self):
        self._setState(MIGRATION_STATE.rollback)
        self._logger.warn("start rollback " + self.__class__.__name__)
        self._rollback()
        self._setState(MIGRATION_STATE.rollbackDone)
        self._logger.info("end rollback " + self.__class__.__name__)

    def _setState(self, state):
        if self.state != MIGRATION_STATE.error or self.state in [
            MIGRATION_STATE.rollback,
            MIGRATION_STATE.rollbackDone,
        ]:
            self.state = state

    def exec_cmd(self, command):
        if not exec_cmd(command):
            self._setState(MIGRATION_STATE.error)
            self._logger.error("error during migration for cmd:", command)


# TODO build guide in confluence
