from flask.ext.babel import gettext
from octoprint_mrbeam.mrb_logger import mrb_logger


class WizardConfig:
    def __init__(self, plugin):
        # Just a random number, but we can't go down anymore, just up.
        # If we want to release Beta, then WIZARD_VERSION_BETA should be a higher number than the old WIZARD_VERSION_STABLE
        self.WIZARD_VERSION_STABLE = (
            22  # v0.9.0: Design Store, Toolset updated, Messaging system, New material settings, GCode deletion (
            # just for the wizard), ...
        )
        self.WIZARD_VERSION_BETA = 21  # v0.7.11: GCode deletion, DXFlib update, ...

        self._logger = mrb_logger("octoprint.plugins.mrbeam.wizard_config")

        self._plugin = plugin
        self._user_manager = plugin._user_manager
        self._plugin_manager = plugin._plugin_manager
        self._settings = plugin._settings

        self._is_welcome_wizard = plugin.isFirstRun()
        self._is_whatsnew_wizard = (
            not plugin.isFirstRun() and not self._plugin.is_beta_channel()
        )
        self._is_beta_news_wizard = (
            not self._plugin.isFirstRun() and self._plugin.is_beta_channel()
        )

        self._current_wizard_config = None

    def get_wizard_version(self):
        if self._plugin.is_beta_channel():
            return self.WIZARD_VERSION_BETA
        else:
            return self.WIZARD_VERSION_STABLE

    def get_wizard_name(self):
        if self._is_welcome_wizard:
            return "WELCOME"
        elif self._is_whatsnew_wizard:
            return "WHATSNEW"
        elif self._is_beta_news_wizard:
            return "BETA_NEWS"
        else:
            return None

    def get_wizard_config_to_show(self):
        wizard_config_to_show = []

        if self._is_welcome_wizard:
            self._current_wizard_config = self._welcome_wizard_config()
        elif self._is_whatsnew_wizard:
            self._current_wizard_config = self._whatsnew_wizard_config()
        elif self._is_beta_news_wizard:
            self._current_wizard_config = self._beta_news_wizard_config()

        for wizard, config in self._current_wizard_config.iteritems():
            required = config.get("required", False)
            if required:
                config.pop("required", None)
                wizard_config_to_show.append(config)

        return wizard_config_to_show

    def get_current_wizard_link_ids(self):
        link_ids = []
        wizard_tabs = {}
        if self._is_welcome_wizard:
            link_ids = [
                "wizard_firstrun_end_link"
            ]  # This one is managed by OctoPrint (the start as well, but we don't want it)
            wizard_tabs = self._welcome_wizard_config()
        elif self._is_whatsnew_wizard:
            wizard_tabs = self._whatsnew_wizard_config()
        elif self._is_beta_news_wizard:
            wizard_tabs = self._beta_news_wizard_config()

        for tab, data in wizard_tabs.iteritems():
            link_ids.append(data["div"] + "_link")

        return link_ids

    def _welcome_wizard_config(self):
        """Add here the tabs that should be present in the welcome wizard.

        The order of the tabs is set in __init__.py > __plugin_load__()
        > __plugin_settings_overlay__['appearance']['order]. The welcome
        and what's new wizard are actually the same wizard, so both are
        configured in the same place.
        """
        welcome_wizard_tabs = dict(
            wizard_wifi=dict(
                type="wizard",
                name=gettext("Connection"),
                required=self._is_wifi_wizard_required(),
                mandatory=False,
                suffix="_wifi",
                template="wizard/wizard_connection.jinja2",
                div="wizard_plugin_corewizard_connection",
            ),
            wizard_acl=dict(
                type="wizard",
                name=gettext("Your user"),
                required=self._is_acl_wizard_required(),
                mandatory=False,
                suffix="_acl",
                template="wizard/wizard_acl.jinja2",
                div="wizard_plugin_corewizard_acl",
            ),
            wizard_lasersafety=dict(
                type="wizard",
                name=gettext("For your safety"),
                required=True,
                mandatory=False,
                suffix="_lasersafety",
                template="wizard/wizard_lasersafety.jinja2",
                div="wizard_plugin_corewizard_lasersafety",
            ),
            wizard_analytics=dict(
                type="wizard",
                name=gettext("Better together"),
                required=self._is_analytics_wizard_required(),
                mandatory=False,
                suffix="_analytics",
                template="wizard/wizard_analytics.jinja2",
                div="wizard_plugin_corewizard_analytics",
            ),
            wizard_guided_tour=dict(
                type="wizard",
                name=gettext("Guided Tour"),
                required=True,
                mandatory=False,
                suffix="_guided_tour",
                template="wizard/wizard_guided_tour.jinja2",
                div="wizard_plugin_corewizard_guided_tour",
            ),
        )

        return welcome_wizard_tabs

    def _whatsnew_wizard_config(self):
        """Add here the tabs that should be present in the what's new wizard.
        Remove when unnecessary. The order of the tabs is set in __init__.py >
        __plugin_load__() > __plugin_settings_overlay__['appearance']['order].
        The welcome and what's new wizard are actually the same wizard, so both
        are configured in the same place.

        Change the "required" to False if that slide should not be
        present in the dialog, revert otherwise.
        """
        whatsnew_wizard_tabs = dict(
            wizard_whatsnew_0=dict(
                type="wizard",
                name=gettext("Design Store"),
                required=True,
                mandatory=False,
                suffix="_whatsnew_0",
                template="wizard/wizard_whatsnew_0.jinja2",
                div="wizard_plugin_corewizard_whatsnew_0",
            ),
            wizard_whatsnew_1=dict(
                type="wizard",
                name=gettext("New Toolset Features"),
                required=True,
                mandatory=False,
                suffix="_whatsnew_1",
                template="wizard/wizard_whatsnew_1.jinja2",
                div="wizard_plugin_corewizard_whatsnew_1",
            ),
            wizard_whatsnew_2=dict(
                type="wizard",
                name=gettext("GCode auto-deletion"),
                required=True,
                mandatory=False,
                suffix="_whatsnew_2",
                template="wizard/wizard_whatsnew_2.jinja2",
                div="wizard_plugin_corewizard_news_gcode",
            ),
            wizard_whatsnew_3=dict(
                type="wizard",
                name=gettext("...and more!"),
                required=True,
                mandatory=False,
                suffix="_whatsnew_3",
                template="wizard/wizard_whatsnew_3.jinja2",
                div="wizard_plugin_corewizard_whatsnew_3",
            ),
            wizard_analytics=dict(
                type="wizard",
                name=gettext("Better together"),
                required=self._is_analytics_wizard_required(),
                mandatory=False,
                suffix="_analytics",
                template="wizard/wizard_analytics.jinja2",
                div="wizard_plugin_corewizard_analytics",
            ),
        )

        # remove gcode deletion screen if it is already enabled
        if self._plugin._settings.get(["gcodeAutoDeletion"]):
            del whatsnew_wizard_tabs["wizard_whatsnew_2"]

        return whatsnew_wizard_tabs

    @staticmethod
    def _beta_news_wizard_config():
        """Add here the tabs that should be present in the beta news wizard.
        Remove when unnecessary. The order of the tabs is set in __init__.py >
        __plugin_load__() > __plugin_settings_overlay__['appearance']['order].
        The welcome, what's new and beta news wizards are actually the same
        wizard, so all are configured in the same place.

        Change the "required" to False if that slide should not be
        present in the dialog, revert otherwise.
        """
        beta_news_wizard_tabs = dict(
            wizard_beta_news_0=dict(
                type="wizard",
                name=gettext("GCode auto-deletion"),
                required=True,
                mandatory=False,
                suffix="_beta_news_0",
                template="wizard/wizard_beta_news_0.jinja2",
                div="wizard_plugin_corewizard_news_gcode",
            ),
        )

        return beta_news_wizard_tabs

    def _is_wifi_wizard_required(self):
        required = False
        try:
            plugin_info = self._plugin_manager.get_plugin_info("netconnectd")
            if plugin_info is not None:
                status = plugin_info.implementation._get_status()
                required = not status["connections"]["wifi"]
        except Exception:
            self._logger.exception(
                "Exception while reading wifi state from netconnectd."
            )

        self._logger.debug("_is_wifi_wizard_required() %s", required)
        return required

    def _is_acl_wizard_required(self):
        required = (
            self._user_manager.enabled and not self._user_manager.hasBeenCustomized()
        )
        self._logger.debug("_is_acl_wizard_required() %s", required)
        return required

    def _is_analytics_wizard_required(self):
        required = self._settings.get(["analyticsEnabled"]) is None
        self._logger.debug("_is_analytics_wizard_required() %s", required)
        return required
