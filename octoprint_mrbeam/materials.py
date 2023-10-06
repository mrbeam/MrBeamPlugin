import os
import yaml

from octoprint_mrbeam.model.custom_material_model import CustomMaterialModel
from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None

# TODO: SW-3719 import these from mode services
DEFAULT_MODE = "default"
ROTARY_MODE = "rotary"


def materials(plugin):
    global _instance
    if _instance is None:
        _instance = Materials(plugin)
    return _instance


class Materials(object):
    FILE_CUSTOM_MATERIALS = "materials.yaml"

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.materials")
        self.plugin = plugin
        self.custom_materials_file = os.path.join(
            self.plugin._settings.getBaseFolder("base"), self.FILE_CUSTOM_MATERIALS
        )

        self.custom_materials = self._load_materials_from_yaml()

    def _load_materials_from_yaml(self):
        custom_materials = {}

        try:
            if os.path.isfile(self.custom_materials_file):
                with open(self.custom_materials_file) as yaml_file:
                    content = yaml.safe_load(yaml_file)
                    custom_materials = content.get("custom_materials", {})

            self._logger.info("{} custom materials loaded".format(len(custom_materials)))
        except Exception as e:
            self._logger.exception("Exception while loading custom materials: {}".format(e))

        return custom_materials

    def _write_materials_to_yaml(self):
        try:
            data = dict(custom_materials=self.custom_materials)
            with open(self.custom_materials_file, "wb") as new_yaml:
                yaml.safe_dump(
                    data,
                    new_yaml,
                    default_flow_style=False,
                    indent="  ",
                    allow_unicode=True,
                )
            self._logger.info("{} custom materials saved".format(len(self.custom_materials)))
        except Exception as e:
            self._logger.exception("Exception while saving custom materials: {}".format(e))

    def get_custom_materials_for_laser_cutter_mode(self):
        """Get currently saved custom materials for a specific laser cutter mode.
        If a material doesn't have a laser_cutter_mode set, default will be assumed.

        Returns: The list of custom materials for the given laser cutter mode

        """
        laser_cutter_mode = self.plugin.get_laser_cutter_mode()
        return {
            key: value for key, value in self.custom_materials.items() if
            value.get('laser_cutter_mode', DEFAULT_MODE) == laser_cutter_mode
        }

    def add_custom_material(self, material_key, material):
        try:
            self._logger.info("Adding custom material: {}".format(material.get("name")))
            custom_material = CustomMaterialModel(
                material_key=material_key,
                material=material,
                laser_cutter_mode=self.plugin.get_laser_cutter_mode(),
                laser_model=self.plugin.get_laser_head_model(),
                plugin_v=self.plugin.get_plugin_version(),
                device_model=self.plugin.get_model_id()
            )
            self.custom_materials[custom_material.material_key] = custom_material.to_dict()
            self._write_materials_to_yaml()
        except Exception as e:
            self._logger.exception("Exception while adding material: {}".format(e))

    def delete_custom_material(self, material_key):
        if material_key in self.custom_materials:
            self._logger.info("Deleting custom material: {}".format(material_key))
            del self.custom_materials[material_key]
            self._write_materials_to_yaml()

    def delete_all_custom_materials(self):
        self._logger.info("Deleting all custom materials")
        self.custom_materials = {}
        self._write_materials_to_yaml()
