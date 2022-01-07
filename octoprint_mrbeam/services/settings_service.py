from flask_babel import gettext

from octoprint_mrbeam.model.settings_model import SettingsModel, About, Document, DocumentLink
from octoprint_mrbeamdoc import MrBeamDocAvailable, MrBeamModel


class SettingsService:
    """
    In this class we gather all the service layer calculations needed regarding settings
    """

    def __init__(self, logger):
        self._logger = logger

    def get_template_settings_model(self, mrbeam_model):
        """
        mrbeam_model String: Name of the running mrbeam_model

        Return SettingsModel containing all the information and settings available for this specific mrbeam_model
        """
        if not mrbeam_model:
            self._logger.error('MrBeamModel not valid -> %s', mrbeam_model)
            return self._empty_settings_model()

        mrbeam_model_found = next((model for model in MrBeamModel if model.value.lower() == mrbeam_model.lower()), None)
        if mrbeam_model_found is None:
            self._logger.error('MrBeamModel not identified %s', mrbeam_model)
            return self._empty_settings_model()

        definitions = MrBeamDocAvailable.get_mrbeam_definitions_for(mrbeam_model_found)
        settings_model = SettingsModel()
        settings_model.about = About([self._get_documents_for_definition(definition) for definition in definitions])
        return settings_model

    def _empty_settings_model(self):
        settings_model = SettingsModel()
        settings_model.about = About([])
        return settings_model

    def _get_documents_for_definition(self, definition):
        document_links = [DocumentLink(language, self._get_url_for_definition_language(definition, language)) for
                          language in definition.supported_languages]
        title_key = definition.mrbeamdoc_type.value
        title_translated = gettext(title_key)
        if title_key == title_translated:
            self._logger.error(
                'No key found for title_key=%(title_key)s title_translated=%(title_translated)s' % {
                    'title_key': title_key,
                    'title_translated': title_translated})
        return Document(title_translated, document_links)

    def _get_url_for_definition_language(self, definition, language, extension='pdf'):
        return '/plugin/mrbeam/docs/%(mrbeam_model)s/%(language)s/%(mrbeam_type)s.%(extension)s' % {
            'mrbeam_model': definition.mrbeam_model.value,
            'language': language.value,
            'mrbeam_type': definition.mrbeamdoc_type.value,
            'extension': extension}
