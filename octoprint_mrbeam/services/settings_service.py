import requests
import yaml
from octoprint.plugin import PluginSettings
from yaml import SafeLoader

from octoprint_mrbeam.decorator.catch_import_error import prevent_execution_on_import_error
from octoprint_mrbeam.model import EmptyImport
from octoprint_mrbeam.software_update_information import SWUpdateTier

try:
    from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils
except ImportError:
    MrBeamDocUtils = EmptyImport("from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils")

from octoprint_mrbeam.model.settings_model import SettingsModel, AboutModel, MaterialStoreModel

MATERIAL_STORE_CONFIG_URL = "https://raw.githubusercontent.com/mrbeam/material-store-settings/master/config.yaml"


def _empty_settings_model():
    settings_model = SettingsModel()
    settings_model.about = AboutModel()
    return settings_model


def get_environment_enum_from_plugin_settings(plugin_settings):
    if type(plugin_settings) is not PluginSettings:
        return SWUpdateTier.STABLE

    if plugin_settings.get(["dev", "env"]) == SWUpdateTier.DEV.value:
        return SWUpdateTier.DEV

    software_tier_value = plugin_settings.get(["dev", "software_tier"])
    if type(software_tier_value) is not str:
        return SWUpdateTier.STABLE

    lower_case_software_tier = software_tier_value.lower()
    if lower_case_software_tier == SWUpdateTier.STABLE.value.lower():
        return SWUpdateTier.STABLE
    elif lower_case_software_tier == SWUpdateTier.BETA.value.lower():
        return SWUpdateTier.BETA
    elif lower_case_software_tier == SWUpdateTier.ALPHA.value.lower():
        return SWUpdateTier.ALPHA

    return SWUpdateTier.STABLE


class SettingsService:
    """
    In this class we gather all the service layer calculations needed regarding settings
    """

    def __init__(self, logger, document_service, environment=SWUpdateTier.STABLE):
        self._logger = logger
        self._document_service = document_service
        self.environment = environment

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
        settings_model.material_store = self._get_material_store_settings(self.environment)
        settings_model.about = AboutModel(
            support_documents=[self._document_service.get_documents_for(definition) for definition in definitions])

        self._logger.info("SettingsModel -> %s", str(settings_model))
        return settings_model

    def _get_material_store_settings(self, environment):
        material_store_settings = MaterialStoreModel()
        try:
            response = requests.get(MATERIAL_STORE_CONFIG_URL, allow_redirects=False)
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
        material_store_config = MaterialStoreModel()
        if self._is_valid_material_store_config(environment, material_store_config_yml):
            env_config_yml = material_store_config_yml['material-store']['environment'][environment.value.lower()]
            material_store_config.enabled = env_config_yml['enabled']
            material_store_config.url = env_config_yml['url']
        else:
            self._logger.warn(
                'Couldn\'t find corresponding material store configuration to current environment -> %s <-',
                environment.value.lower())

        return material_store_config

    def _is_valid_material_store_config(self, environment, material_store_config_yml):
        return environment and material_store_config_yml and ('material-store' in material_store_config_yml) and (
                'environment' in material_store_config_yml['material-store']) and (
                       environment.value.lower() in material_store_config_yml['material-store']['environment']) and (
                       'enabled' in material_store_config_yml['material-store']['environment'][
                   environment.value.lower()]) and ('url' in material_store_config_yml['material-store']['environment'][
            environment.value.lower()])
