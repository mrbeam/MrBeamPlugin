import threading
import logging


class ConnectivityChecker(object):
    """Abstraction of Octoprints connectivity checker 'util/__init__.py #1300'"""

    def __init__(self, plugin):
        self._check_worker = None
        self._check_mutex = threading.RLock()
        self._plugin = plugin

        self._logger = logging.getLogger(
            "octoprint.plugins." + __name__ + ".connectivity_checker"
        )

    @property
    def online(self):
        """

        Args:

        Returns:
          boolean: is the device connected to the internet, returns None if the octoprint checker is disabled

        """
        with self._check_mutex:
            # if the octoprint connectivity checker is disabled return None instead of true
            if self._plugin._octoprint_connectivity_checker.enabled:
                # returns the value of the octoprint connectifity checker, this value returns true if the octoprint onlinechecker is disabled
                return self._plugin._octoprint_connectivity_checker.online
            else:
                return None

    def check_immediately(self):
        """
        checks immediatley for a internet connection and don't wait for the interval

        Args:

        Returns:
          boolean: is the device connected to the internet

        """
        with self._check_mutex:
            # calls the octoprint check_immediately methode to run the checker immediately
            self._plugin._octoprint_connectivity_checker.check_immediately()
            return self.online
