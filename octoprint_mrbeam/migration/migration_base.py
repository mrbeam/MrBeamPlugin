import abc, six
import os
from abc import abstractmethod
from distutils.version import LooseVersion

from octoprint_mrbeam import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd


# TODO build guide in confluence


class MIGRATION_STATE(enumerate):
    init = 1
    migration_started = 2
    migration_done = 3
    rollback_started = 4
    rollback_done = 5
    error = -1
    rollback_error = -2


class MigrationException(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class MigrationBaseClass:
    # folder of the files needed during migration
    MIGRATE_FILES_FOLDER = os.path.join("files/migrate/")

    # lowest beamos version that should run the migration
    BEAMOS_VERSION_LOW = None
    # highest beamos version that should run the migration
    BEAMOS_VERSION_HIGH = None

    def __init__(self, plugin):
        self.plugin = plugin
        self._state = MIGRATION_STATE.init
        self._logger = mrb_logger(
            "octoprint.plugins.mrbeam.migrate." + self.__class__.__name__
        )

    @property
    @abstractmethod
    def id(self):
        """
        return the id of this migration step
        @return:
        """
        # TODO return correct migration id regex from filename
        return None

    @staticmethod
    def shouldrun(cls, beamos_version):
        """
        @param cls: Migrationclass
        @param beamos_version: current beamos_version
        @param plugin: Mr Beam Plugin instance
        @return: boolean if this migration should run
        """
        if (
            LooseVersion(cls.BEAMOS_VERSION_LOW)
            <= LooseVersion(beamos_version)
            <= LooseVersion(cls.BEAMOS_VERSION_HIGH)
        ):
            return True
        else:
            return False

    @staticmethod
    def return_obj(cls, plugin):
        """
        @return: new instance of the class
        """
        new_instance = cls(plugin)
        return new_instance

    @abc.abstractmethod
    @abstractmethod
    def _run(self):
        """
        this class should be witten in the childclasses it will be executed as migration
        @return: boolean if successfull
        """
        return True

    @abstractmethod
    def _rollback(self):
        """
        this class should be written in the childclasses it will be executed as rollback
        @return: boolean if successfull
        """
        return True

    def run(self):
        """
        this will wrap the migration execution
        @return:
        """
        self._setState(MIGRATION_STATE.migration_started)
        self._logger.info("start migration of " + self.__class__.__name__)
        try:
            self._run()
            self._setState(MIGRATION_STATE.migration_done)
            self._logger.info("end migration of " + self.__class__.__name__)
        except MigrationException as e:
            self._setState(MIGRATION_STATE.error)
            self._logger.error("error during migration {}".format(e))
        except Exception as e:
            self._logger.exception("exception during migration: {}".format(e))
            self.rollback()

    def rollback(self):
        """
        this will wrap the rollback execution
        @return:
        """
        self._setState(MIGRATION_STATE.rollback_started)
        self._logger.warn("start rollback " + self.__class__.__name__)

        try:
            self._rollback()
            self._setState(MIGRATION_STATE.rollback_done)
            self._logger.info("end rollback " + self.__class__.__name__)
        except MigrationException as e:
            self._setState(MIGRATION_STATE.rollback_error)
            self._logger.exception("exception during rollback: {}".format(e))

    def _setState(self, state):
        """
        sets the state of the migration
        @param state: new state
        @return:
        """
        if self._state != MIGRATION_STATE.error or self._state in [
            MIGRATION_STATE.rollback_started,
            MIGRATION_STATE.rollback_done,
            MIGRATION_STATE.rollback_error,
        ]:
            self._state = state

    @property
    def state(self):
        return self._state

    def exec_cmd(self, command):
        """
        wrapper of exec_cmd to change to errorstate in case of a error
        @param command:
        @return:
        """
        if not exec_cmd(command):
            raise MigrationException("error during migration for cmd:", command)
