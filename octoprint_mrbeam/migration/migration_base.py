import abc, six
import os
from abc import abstractmethod
from distutils.version import LooseVersion

from octoprint_mrbeam import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd


# TODO build guide in confluence


class MIGRATION_STATE(enumerate):
    """
    enum of the different migraton states
    """

    init = 1
    migration_started = 2
    migration_done = 3
    rollback_started = 4
    rollback_done = 5
    error = -1
    rollback_error = -2


class MIGRATION_RESTART(enumerate):
    NONE = 0
    DEVICE = 1
    OCTOPRINT = 2


class MigrationException(Exception):
    """
    Exception that could occure during migration
    """

    pass


@six.add_metaclass(abc.ABCMeta)
class MigrationBaseClass:
    """
    Base Class of a migration, this has to be extended in a childclass for each migration that should run
    """

    # folder of the files needed during migration
    MIGRATE_FILES_FOLDER = os.path.join("files/migrate/")

    # lowest beamos version that should run the migration
    BEAMOS_VERSION_LOW = None
    # highest beamos version that should run the migration
    BEAMOS_VERSION_HIGH = None

    def __init__(self, plugin, restart=MIGRATION_RESTART.NONE):
        """
        initalization of the class

        Args:
            plugin: Mr Beam Plugin
        """
        self.plugin = plugin
        self._state = MIGRATION_STATE.init
        self._logger = mrb_logger(
            "octoprint.plugins.mrbeam.migrate." + self.__class__.__name__
        )
        self.restart = restart

    @property
    @abstractmethod
    def id(self):
        """
        return the id of this migration step

        Returns:
            string: id of this migration step
        """
        # TODO return correct migration id regex from filename
        return None

    @staticmethod
    def shouldrun(cls, beamos_version):
        """
        Checks if this Miration should run

        Args:
            cls: Migrationclass
            beamos_version: current beamos_version

        Returns:
            bool: True if this migration should run
        """
        if not isinstance(beamos_version, basestring):
            mrb_logger(
                "octoprint.plugins.mrbeam.migrate.{}".format(cls.__name__)
            ).error("beamos_version is not a string: {}".format(beamos_version))
            return False
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
        returns a instance of the Class

        Args:
            cls: class
            plugin: Mr Beam Plugin

        Returns:
            objct: new instance of the class
        """
        new_instance = cls(plugin)
        return new_instance

    @abc.abstractmethod
    @abstractmethod
    def _run(self):
        """
        this class should be witten in the childclasses it will be executed as migration
        Returns:
            bool: True if successfull
        """
        return True

    @abstractmethod
    def _rollback(self):
        """
        this class should be written in the childclasses it will be executed as rollback
        Returns:
            bool: True if successfull
        """
        return True

    def run(self):
        """
        this will wrap the migration execution

        Returns:
            None
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
        Returns:
            None
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
        Args:
            state: new state

        Returns:
            None
        """
        if self._state != MIGRATION_STATE.error or self._state in [
            MIGRATION_STATE.rollback_started,
            MIGRATION_STATE.rollback_done,
            MIGRATION_STATE.rollback_error,
        ]:
            self._state = state

    @property
    def state(self):
        """
        returns state

        Returns:
            state
        """
        return self._state

    def exec_cmd(self, command, optional=False):
        """
        wrapper of exec_cmd to change to errorstate in case of a error
        Args:
            command: command to be executed

        Returns:
            None
        Raises:
            MigrationException: if the execution of the command was not successful
        """
        command_success = exec_cmd(command)
        if command_success:
            return
        if optional and not command_success:
            self._logger.warn("optional command failed - cmd: {}".format(command))
        else:
            raise MigrationException(
                "error during migration for cmd: {} - return: {}".format(
                    command, command_success
                )
            )

    @staticmethod
    def execute_restart(restart):
        logger = mrb_logger("octoprint.plugins.mrbeam.migrate.restart")
        if restart:
            if restart == MIGRATION_RESTART.OCTOPRINT:
                logger.info("restart octoprint after migration")
                exec_cmd("sudo systemctl restart octoprint.service")
            elif restart == MIGRATION_RESTART.DEVICE:
                logger.info("restart device after migration")
                exec_cmd("sudo reboot now")
            else:
                logger.info(
                    "restart after migration choosen but unknown type: {}".format(
                        restart
                    )
                )
