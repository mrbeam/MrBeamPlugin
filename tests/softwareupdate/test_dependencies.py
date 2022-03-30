import os
import re
import unittest


class TestUpdateScript(unittest.TestCase):
    def test_dependencies_file(self):
        dependencies_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../octoprint_mrbeam/dependencies.txt",
        )
        dependencies_pattern = r"([a-z]+(?:[_-][a-z]+)*)==((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
        with open(dependencies_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                self.assertRegexpMatches(line, dependencies_pattern)
