import unittest

from octoprint_mrbeam.util.version_comparator import VersionComparator, COMPARISON_OPTIONS
from octoprint_mrbeam.software_update_information import (
    _generate_config_of_beamos,
    get_config_for_version,
)


class VersionComparisonTestCase(unittest.TestCase):
    def setUp(self):
        self.le_element = {"__le__": {"0.17.0": {"value": 3}}}
        self.ge_element = {
            "__ge__": {
                "0.18.0": {"value": 2},
                "0.14.0": {"value": 1},
                "0.18.1": {"value": 5},
                "1.0.0": {"value": 6},
            }
        }
        self.eq_element = {"__eq__": {"0.16.5": {"value": 4}}}
        self.config = {}
        self.config.update(self.ge_element)
        self.config.update(self.le_element)
        self.config.update(self.eq_element)
        self.comparison_options = COMPARISON_OPTIONS

    def test_sorted(self):
        print(self.config)
        config = sorted(
            self.config,
            cmp=lambda comp1, comp2: cmp(
                VersionComparator.get_comparator(comp1, self.comparison_options).priority,
                VersionComparator.get_comparator(comp2, self.comparison_options).priority
            ),
        )
        self.assertEquals(config, ["__ge__", "__le__", "__eq__"]),

    def test_compare(self):
        config = sorted(
            self.config.items(),
            key=lambda com: VersionComparator.get_comparator(
                com[0], self.comparison_options
            ).priority,
        )
        print(config)

        self.assertEquals(
            2,
            get_config_for_version("0.18.0", config).get(
                "value"
            ),
        )
        self.assertEquals(
            1,
            get_config_for_version("0.17.1", config).get(
                "value"
            ),
        )
        self.assertEquals(
            3,
            get_config_for_version("0.16.8", config).get(
                "value"
            ),
        )
        self.assertEquals(
            4,
            get_config_for_version("0.16.5", config).get(
                "value"
            ),
        )
        self.assertEquals(
            5,
            get_config_for_version("0.18.2", config).get(
                "value"
            ),
        )
        self.assertEquals(
            6,
            get_config_for_version("1.0.0", config).get(
                "value"
            ),
        )
        # only support major minor patch so far
        # self.assertEquals(
        #     1,
        #     get_config_for_version("0.17.5.pre0", config).get(
        #         "value"
        #     ),
        # )
        # self.assertEquals(
        #     1,
        #     get_config_for_version("0.18.0a0", config).get(
        #         "value"
        #     ),
        # )

    def test_generate_config_of_beamos(self):
        config = {
            "repo": "netconnectd_mrbeam",
            "pip": "https://github.com/mrbeam/netconnectd_mrbeam/archive/{target_version}.zip",
            "global_pip_command": True,
            "beamos_date": {
                "2021-06-11": {
                    "pip_command": "sudo /usr/local/netconnectd/venv/bin/pip"
                }
            },
            "beamos_version": {
                "__ge__": {
                    "0.18.0": {
                        "pip_command": "sudo /usr/local/netconnectd/venv/bin/pip"
                    }
                },
                "__le__": {"0.14.0": {"version": "0.0.1"}},
            },
        }

        self.assertEquals(
            _generate_config_of_beamos(config, "0.14.0", "stable").get("version"),
            "0.0.1",
        )
        self.assertEquals(
            _generate_config_of_beamos(config, "0.18.0", "stable").get("version"), None
        )
