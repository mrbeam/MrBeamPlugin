from octoprint_mrbeam.mrb_logger import mrb_logger

class LaserCutterProfileModel(object):
    """Laser cutter profile model."""

    def __init__(self, profile=None):
        """Initialize laser cutter profile.

        If the profile is not found in the defined profiles, it will fall back to default.

        Args:
            profile (dict): The profile of the laser cutter.
        """
        self._logger = mrb_logger("octoprint.plugins.mrbeam.model.laser_cutter_profile")
        self._data = profile

    @property
    def data(self):
        return self._data
