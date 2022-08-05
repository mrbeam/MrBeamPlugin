import os
import yaml
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util import dict_get


# singleton
_instance = None


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

        self.custom_materials = dict()
        self.custom_materials_loaded = False

    def get_custom_materials(self):
        """
        Get list of currently saved custom materials
        :return:
        """
        self._load()
        return self.custom_materials

    def put_custom_material(self, key, material):
        """
        Sanitize and put material. If key exists, material will be overwritten
        :param key: String unique material key
        :param material: Dict of material data
        :return: Boolean success
        """
        self._load()
        res = None

        try:
            if dict_get(material, ['laser_type']) == "MrBeamII-1.0":
                material["laser_model"] = '0'
                del material["laser_type"]
            if "model" in material:
                material["device_model"] = material.pop("model")
            if "compatible" in material:
                material.pop("compatible")
            if "customBeforeElementContent" in material:
                material.pop("customBeforeElementContent")

            self.custom_materials[key.strip()] = material
            res = True
        except:
            self._logger.exception(
                "Exception while putting materials: key: %s, data: %s", key, material
            )
            res = False
        if res:
            res = self._save()
        return res

    def delete_custom_material(self, key):
        """
        Deletes custom material if existing.
        :param keys: String or list: key or list of keys to delete
        :return: Boolean success
        """
        self._load()
        count = 0
        res = True

        key_list = key
        if isinstance(key_list, basestring):
            key_list = [key_list]

        if key_list:
            try:
                for k in key_list:
                    try:
                        del self.custom_materials[k]
                        count += 1
                    except ValueError:
                        pass
            except:
                self._logger.exception(
                    "Exception while deleting materials: key: %s", key
                )
                res = False
            if res and count > 0:
                res = self._save()
        return res

    def reset_all_custom_materials(self):
        self._logger.info("Resetting all custom material settings!!!!")
        self.custom_materials = {}
        self._save(force=True)

    def _load(self, force=False):
        if not self.custom_materials_loaded or force:
            try:
                if os.path.isfile(self.custom_materials_file):
                    with open(self.custom_materials_file) as yaml_file:
                        tmp = yaml.safe_load(yaml_file)
                        self.custom_materials = (
                            tmp["custom_materials"]
                            if tmp and "custom_materials" in tmp
                            else dict()
                        )
                    self._logger.debug(
                        "Loaded %s custom materials from file %s",
                        len(self.custom_materials),
                        self.custom_materials_file,
                    )
                else:
                    self.custom_materials = dict()
                    self._logger.debug(
                        "No custom materials yet. File %s does not exist.",
                        self.custom_materials_file,
                    )
                self.custom_materials_loaded = True
            except Exception as e:
                self._logger.exception(
                    "Exception while loading custom materials from file {}".format(
                        self.custom_materials_file
                    )
                )
                self.custom_materials = dict()
                self.custom_materials_loaded = False
        return self.custom_materials

    def _save(self, force=False):
        if not self.custom_materials_loaded and not force:
            raise Exception("You need to load custom_materials before trying to save.")
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
            self.custom_materials_loaded = True
            self._logger.debug(
                "Saved %s custom materials (in total) to file %s",
                len(self.custom_materials),
                self.custom_materials_file,
            )
        except:
            self._logger.exception(
                "Exception while writing custom materials to file %s",
                self.custom_materials_file,
            )
            self.custom_materials_loaded = False
            return False
        return True
