import requests
import yaml
from yaml import SafeLoader

from octoprint_mrbeam.decorator.catch_import_error import prevent_execution_on_import_error
from octoprint_mrbeam.model import EmptyImport

try:
    from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils
except ImportError:
    MrBeamDocUtils = EmptyImport("from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils")

from octoprint_mrbeam.model.settings_model import SettingsModel, AboutModel, MaterialStore


def _empty_settings_model():
    settings_model = SettingsModel()
    settings_model.about = AboutModel()
    return settings_model


class SettingsService:
    """
    In this class we gather all the service layer calculations needed regarding settings
    """

    def __init__(self, logger, document_service):
        self._logger = logger
        self._document_service = document_service

    @prevent_execution_on_import_error(MrBeamDocUtils, callable=_empty_settings_model)
    def get_template_settings_model(self, mrbeam_model):
        """
        mrbeam_model String: Name of the running mrbeam_model

        Return SettingsModel containing all the information and settings available for this specific mrbeam_model
        """
        mrbeam_model_found = MrBeamDocUtils.get_mrbeam_model_enum_for(mrbeam_model)
        if mrbeam_model_found is None:
            self._logger.error('MrBeamModel not identified %s', mrbeam_model)
            return _empty_settings_model()

        definitions = MrBeamDocUtils.get_mrbeam_definitions_for(mrbeam_model_found)
        settings_model = SettingsModel()
        settings_model.material_store = self._get_material_store_settings("localhost")
        settings_model.about = AboutModel(
            support_documents=[self._document_service.get_documents_for(definition) for definition in definitions])
        return settings_model

    def _get_material_store_settings(self, environment):

        material_store_config_url = "https://raw.githubusercontent.com/mrbeam/material-store-settings/master/config.yaml"
        material_store_settings = MaterialStore()
        try:
            response = requests.get(material_store_config_url, allow_redirects=False)
        except requests.exceptions.RequestException as e:
            self._logger.error('Material store settings couldn\'t be retrieved. Exception %s', e)
        else:
            if response.ok:
                try:
                    material_store_config_yml = yaml.load(response.content, Loader=SafeLoader)
                    material_store_config = self._get_material_store_config_from_yml(material_store_config_yml,
                                                                                     environment)
                    material_store_settings.enabled = material_store_config.enabled
                    material_store_settings.url = material_store_config.url
                except yaml.YAMLError as e:
                    self._logger.error('Material store settings couldn\'t be parsed. Exception %s', e)

        return material_store_settings

    def _get_material_store_config_from_yml(self, material_store_config_yml, environment):
        material_store_config = MaterialStore()
        if material_store_config_yml['material-store'] and material_store_config_yml['material-store'][
            'environment'] and material_store_config_yml['material-store']['environment'][environment]:
            env_config_yml = material_store_config_yml['material-store']['environment'][environment]
            material_store_config.enabled = env_config_yml['enabled']
            material_store_config.url = env_config_yml['url']

        return material_store_config
