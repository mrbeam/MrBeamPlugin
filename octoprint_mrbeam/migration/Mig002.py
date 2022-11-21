from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
    MIGRATION_RESTART,
)


class Mig002EnableOnlineCheck(MigrationBaseClass):
    """
    Migration for beamos versions 0.0.0 up to 0.18.2 to enable online check
    """

    BEAMOS_VERSION_LOW = "0.0.0"
    BEAMOS_VERSION_HIGH = "0.18.2"

    def __init__(self, plugin):
        """
        initalization of the migration 002

        Args:
            plugin: Mr Beam Plugin
        """
        super(Mig002EnableOnlineCheck, self).__init__(
            plugin, restart=MIGRATION_RESTART.OCTOPRINT
        )

    @property
    def id(self):
        """
        return the id of the migration

        Returns:
            string: id of the migration
        """
        return "002"

    def _run(self):
        """
        migration steps executet during migration

        Returns:
            None
        """
        self._logger.debug("change config to enable online check")
        self.plugin._settings.global_set(
            ["server", "onlineCheck", "enabled"],
            True,
        )
        self.plugin._settings.global_set(
            ["server", "onlineCheck", "host"],
            "find.mr-beam.org",
        )
        self.plugin._settings.global_set(
            ["server", "onlineCheck", "port"],
            "80",
        )
        self.plugin._settings.save()

        super(Mig002EnableOnlineCheck, self)._run()

    def _rollback(self):
        """
        rollback steps executet during rollback

        Returns:
            None
        """
        # self._logger.debug("disable online check")
        self.plugin._settings.global_set(
            ["server", "onlineCheck", "enabled"],
            False,
        )
        self.plugin._settings.save()

        super(Mig002EnableOnlineCheck, self)._rollback()
