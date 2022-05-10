from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils

from octoprint_mrbeam.model.settings_model import SettingsModel, AboutModel


class SettingsService:
    """
    In this class we gather all the service layer calculations needed regarding settings
    """

    def __init__(self, logger, document_service):
        self._logger = logger
        self._document_service = document_service

    def get_template_settings_model(self, mrbeam_model):
        """
        mrbeam_model String: Name of the running mrbeam_model

        Return SettingsModel containing all the information and settings available for this specific mrbeam_model
        """
        mrbeam_model_found = MrBeamDocUtils.get_mrbeam_model_enum_for(mrbeam_model)
        if mrbeam_model_found is None:
            self._logger.error('MrBeamModel not identified %s', mrbeam_model)
            return self._empty_settings_model()

        definitions = MrBeamDocUtils.get_mrbeam_definitions_for(mrbeam_model_found)
        settings_model = SettingsModel()
        settings_model.about = AboutModel(
            support_documents=[self._document_service.get_documents_for(definition) for definition in definitions])
        return settings_model

    def _empty_settings_model(self):
        settings_model = SettingsModel()
        settings_model.about = AboutModel()
        return settings_model
