from http.client import NO_CONTENT

import octoprint

from octoprint_mrbeam.software_update_information import reload_update_info


class UpdateRestHandlerMixin:
    """
    This class contains all the rest handlers and endpoints related to software update
    """

    @octoprint.plugin.BlueprintPlugin.route("/fetch_update_info", methods=["GET"])
    def fetch_update_info(self):
        reload_update_info(self)
        return NO_CONTENT
