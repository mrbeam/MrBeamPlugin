
import os
import yaml
from octoprint_mrbeam.mrb_logger import mrb_logger


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
		self.custom_materials_file = os.path.join(self.plugin._settings.getBaseFolder('base'), self.FILE_CUSTOM_MATERIALS)

		self.custom_materials = []
		self.custom_materials_loaded = False


	def get_custom_materials(self):
		"""
		Get list of currently saved custom materials
		:return:
		"""
		self._load()
		return self.custom_materials


	def put_custom_materials(self, put_materials):
		"""
		Put array of materials to custom materials. Adds or overwrites
		:param put_materials: list of strings
		:return: number of processed materials
		"""
		self._load()
		count = 0
		res = True

		if put_materials:
			for m in put_materials:
				i = -1
				try:
					i = self.custom_materials.index(m)
				except ValueError:
					pass
				if i < 0:
					# material is new
					self.custom_materials.append(m)
				else:
					# update material
					self.custom_materials[i] = m
				count += 1
			res = self._save()
		return count if res else -1

	def delete_custom_materials(self, del_materials):
		"""
		Deletes custom materials if existing. If material is not fount it's skipped
		:param del_materials: list of strings
		:return: number of deleted materials
		"""
		self._load()
		count = 0
		res = True

		if del_materials:
			for m in del_materials:
				try:
					self.custom_materials.remove(m)
					count += 1
				except ValueError:
					pass
			res = self._save()
		return count if res else -1


	def _load(self, force=False):
		if not self.custom_materials_loaded or force:
				try:
					if os.path.isfile(self.custom_materials_file):
						with open(self.custom_materials_file) as yaml_file:
							tmp = yaml.safe_load(yaml_file)
							self.custom_materials = tmp['custom_materials']
						self._logger.debug("Loaded %s custom materials from file %s", len(self.custom_materials), self.custom_materials_file)
					else:
						self.custom_materials = []
						self._logger.debug("No custom materials yet. File %s does not exist.", self.custom_materials_file)
					self.custom_materials_loaded = True
				except:
					self._logger.exception("Exception while loading custom materials from file %s", self.custom_materials_file)
					self.custom_materials = []
					self.custom_materials_loaded = False
		return self.custom_materials


	def _save(self, force=False):
		if not self.custom_materials_loaded and not force:
			raise Exception("You need to load custom_materials before trying to save.")
		try:
			data = dict(custom_materials=self.custom_materials)
			with open(self.custom_materials_file, 'wb') as new_yaml:
				yaml.safe_dump(data, new_yaml, default_flow_style=False, indent="  ", allow_unicode=True)
			self.custom_materials_loaded = True
			self._logger.debug("Saved %s custom materials (in total) to file %s", len(self.custom_materials), self.custom_materials_file)
		except:
			self._logger.exception("Exception while writing custom materials to file %s", self.custom_materials_file)
			self.custom_materials_loaded = False
			return False
		return True



