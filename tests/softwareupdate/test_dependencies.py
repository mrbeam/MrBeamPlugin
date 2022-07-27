import os
import re
import unittest


class TestUpdateScript(unittest.TestCase):
    def test_dependencies_file(self):
        dependencies_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../octoprint_mrbeam/dependencies.txt",
        )
        dependencies_pattern = r"([a-z]+(?:[_-][a-z]+)*)==(([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$)"  # $ ad the end needed so we see if there is a leftover at the end
        with open(dependencies_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                self.assertRegexpMatches(line, dependencies_pattern)
