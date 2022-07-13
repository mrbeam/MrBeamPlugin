import operator

# singleton
import pkg_resources

from octoprint_mrbeam.mrb_logger import mrb_logger

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
    def get_comparator(comparison_string, comparison_options):
        """
        returns the comparator of the given list of VersionComparator with the matching identifier
        Args:
            comparison_string (str): identifier to search for
            comparison_options (list): list of VersionComparator objects
        Returns:
            object: matching VersionComparator object
        """
        for item in comparison_options:
            if item.identifier == comparison_string:
                return item

def compare_pep440_versions(v1, v2, comparator):
    """
        returns the PEP440 version comparison Boolean result

        Args:
            v1 (str): First version to be compared
            v2 (str): Second version to be compared
            comparator (str): Comparison operator

        Returns:
            Boolean: PEP440 version comparison result
    """
    _logger = mrb_logger("octoprint.plugins.mrbeam." + __name__ + ".compare_pep440_versions")
    try:
        parsed_version_v1 = pkg_resources.parse_version(v1)
        parsed_version_v2 = pkg_resources.parse_version(v2)
        result = VersionComparator.get_comparator(
            comparator, COMPARISON_OPTIONS
        ).compare(parsed_version_v1, parsed_version_v2)
        return result
    except Exception as e:
        _logger.exception("Exception while comparing PEP440 versions: %s", e)
        return None


COMPARISON_OPTIONS = [
    VersionComparator("__eq__", 5, operator.eq),
    VersionComparator("__le__", 4, operator.le),
    VersionComparator("__lt__", 3, operator.lt),
    VersionComparator("__ge__", 2, operator.ge),
    VersionComparator("__gt__", 1, operator.gt),
]
