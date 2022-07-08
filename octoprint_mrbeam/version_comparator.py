from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None


def version_comparator(plugin):
    global _instance
    if _instance is None:
        _instance = VersionComparator(plugin)
    return _instance


class VersionComparator:
    """
    Version Comperator class to compare two versions with the compare method
    """

    def __init__(self, identifier, priority, compare):
        self.identifier = identifier
        self.priority = priority
        self.compare = compare

    @staticmethod
    def get_comparator(comparision_string, comparision_options):
        """
        returns the comperator of the given list of VersionComparator with the matching identifier

        Args:
            comparision_string (str): identifier to search for
            comparision_options (list): list of VersionComparator objects

        Returns:
            object: matching VersionComparator object
        """
        for item in comparision_options:
            if item.identifier == comparision_string:
                return item
