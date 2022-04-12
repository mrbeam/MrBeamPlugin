import unittest

import pkg_resources

from octoprint_mrbeam.software_update_information import (
    VersionComperator,
    _generate_config_of_beamos,
)


def bla(comp1, comparision_options):
    return VersionComperator.get_comperator(comp1, comparision_options).priority


class VersionCaomparisionTestCase(unittest.TestCase):
    def setUp(self):
        self.le_element = {"__le__": {"0.17.0": {"value": 3}}}
        self.ge_element = {"__ge__": {"0.18.0": {"value": 2}, "0.14.0": {"value": 1}}}
        self.eq_element = {"__eq__": {"0.16.5": {"value": 4}}}
        self.config = {}
        self.config.update(self.ge_element)
        self.config.update(self.le_element)
        self.config.update(self.eq_element)
        self.comparision_options = [
            VersionComperator("__eq__", 5, lambda a, b: a == b),
            VersionComperator("__le__", 4, lambda a, b: a <= b),
            VersionComperator("__lt__", 3, lambda a, b: a < b),
            VersionComperator("__ge__", 2, lambda a, b: a >= b),
            VersionComperator("__gt__", 1, lambda a, b: a > b),
        ]

    def test_sorted(self):
        print(self.config)
        config = sorted(
            self.config,
            cmp=lambda comp1, comp2: cmp(
                bla(comp1, self.comparision_options),
                bla(comp2, self.comparision_options),
            ),
            # key=lambda com: VersionComperator.get_comperator(
            #     com[0], self.comparision_options
            # ).priority,
        )
        self.assertEquals(config, ["__ge__", "__le__", "__eq__"]),

    def test_compare(self):
        config = sorted(
            self.config.items(),
            # cmp=lambda comp1, comp2: cmp(
            #     bla(comp1, comparision_options), bla(comp2, comparision_options)
            # ),
            key=lambda com: VersionComperator.get_comperator(
                com[0], self.comparision_options
            ).priority,
        )
        print(config)

        self.assertEquals(2, self.get_value_for_version("0.18.1", config))
        self.assertEquals(1, self.get_value_for_version("0.17.1", config))
        self.assertEquals(3, self.get_value_for_version("0.16.8", config))
        self.assertEquals(4, self.get_value_for_version("0.16.5", config))

    def get_value_for_version(self, target_version, config):
        retvalue = None
        for comp, comp_config in config:
            sorted_comp_config = sorted(
                comp_config.items(), key=lambda ver: pkg_resources.parse_version(ver[0])
            )
            print("sorted", sorted_comp_config)
            for check_version, version_config in sorted_comp_config:
                if VersionComperator.get_comperator(
                    comp, self.comparision_options
                ).comparision(target_version, check_version):
                    retvalue = version_config.get("value")
        return retvalue

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
