from octoprint.server import NO_CONTENT

import octoprint.plugin

from octoprint_mrbeam.software_update_information import reload_update_info


class UpdateRestHandlerMixin:
    """
    This class contains all the rest handlers and endpoints related to software update
    """

    @octoprint.plugin.BlueprintPlugin.route("/info/update", methods=["POST"])
    def update_update_informations(self):
        reload_update_info(self)
        return NO_CONTENT
