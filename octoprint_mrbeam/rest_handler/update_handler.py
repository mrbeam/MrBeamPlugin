from flask import request

import octoprint.plugin

from octoprint_mrbeam.software_update_information import reload_update_info


class UpdateRestHandlerMixin:
    """
    This class contains all the rest handlers and endpoints related to software update
    """

    @octoprint.plugin.BlueprintPlugin.route("/info/update", methods=["POST"])
    def update_update_informations(self):
        clicked_by_user = False
        if hasattr(request, "json") and request.json:
            data = request.json
            clicked_by_user = data.get("user", False)
        reload_update_info(self, clicked_by_user)
        return self._plugin_manager.get_plugin_info(
            "softwareupdate"
        ).implementation.check_for_update()
