import operator
import unittest

import pkg_resources

from octoprint_mrbeam.software_update_information import (
    VersionComperator,
    _generate_config_of_beamos,
    get_config_for_version,
)


def bla(comp1, comparision_options):
    return VersionComperator.get_comperator(comp1, comparision_options).priority


class VersionCaomparisionTestCase(unittest.TestCase):
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
        self.comparision_options = [
            VersionComperator("__eq__", 5, operator.eq),
            VersionComperator("__le__", 4, operator.le),
            VersionComperator("__lt__", 3, operator.lt),
            VersionComperator("__ge__", 2, operator.ge),
            VersionComperator("__gt__", 1, operator.gt),
        ]

    def test_sorted(self):
        print(self.config)
        config = sorted(
            self.config,
            cmp=lambda comp1, comp2: cmp(
                bla(comp1, self.comparision_options),
                bla(comp2, self.comparision_options),
            ),
        )
        self.assertEquals(config, ["__ge__", "__le__", "__eq__"]),

    def test_compare(self):
        config = sorted(
            self.config.items(),
            key=lambda com: VersionComperator.get_comperator(
                com[0], self.comparision_options
            ).priority,
        )
        print(config)

        self.assertEquals(
            2,
            get_config_for_version("0.18.0", config, self.comparision_options).get(
                "value"
            ),
        )
        self.assertEquals(
            1,
            get_config_for_version("0.17.1", config, self.comparision_options).get(
                "value"
            ),
        )
        self.assertEquals(
            3,
            get_config_for_version("0.16.8", config, self.comparision_options).get(
                "value"
            ),
        )
        self.assertEquals(
            4,
            get_config_for_version("0.16.5", config, self.comparision_options).get(
                "value"
            ),
        )
        self.assertEquals(
            5,
            get_config_for_version("0.18.2", config, self.comparision_options).get(
                "value"
            ),
        )
        self.assertEquals(
            6,
            get_config_for_version("1.0.0", config, self.comparision_options).get(
                "value"
            ),
        )
        # only support major minor patch so far
        # self.assertEquals(
        #     1,
        #     get_config_for_version("0.17.5.pre0", config, self.comparision_options).get(
        #         "value"
        #     ),
        # )
        # self.assertEquals(
        #     1,
        #     get_config_for_version("0.18.0a0", config, self.comparision_options).get(
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
