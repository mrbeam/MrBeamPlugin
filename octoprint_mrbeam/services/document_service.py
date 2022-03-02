from flask_babel import get_locale, gettext

from octoprint_mrbeam.model.document_model import DocumentLinkModel, DocumentModel, DocumentSimpleModel
from octoprint_mrbeam.util import string_util


class DocumentService:
    """
    In this class we gather all the service layer calculations needed regarding documents
    """

    def __init__(self, logger):
        self._logger = logger

    def get_documents_for(self, definition):
        """
        Get document information corresponding to a definition

        definition MrBeamDocDefinition: definition of the document

        return DocumentModel corresponding to the requested params
        """
        document_links = [DocumentLinkModel(language, self._get_url_for_definition_language(definition, language)) for
                          language in definition.supported_languages]
        title_translated = self._get_title_translated(definition)
        return DocumentModel(title_translated, document_links)

    def get_document_simple_for(self, definition, language):
        """
        Get a simplified version of the document corresponding to a definition and language

        definition MrBeamDocDefinition: definition of the document
        language SupportedLanguage: language of the document

        return DocumentSimpleModel corresponding to the requested params
        """
        document_link = DocumentLinkModel(language, self._get_url_for_definition_language(definition, language))
        title_translated = self._get_title_translated(definition)
        return DocumentSimpleModel(title_translated, document_link)

    def _get_title_translated(self, definition):
        title_key = string_util.separate_camelcase_words(definition.mrbeamdoc_type.value)
        title_translated = gettext(title_key)
        if get_locale() is not None and get_locale().language != 'en' and title_key == title_translated:
            self._logger.error(
                'No key found for title_key=%(title_key)s title_translated=%(title_translated)s' % {
                    'title_key': title_key,
                    'title_translated': title_translated})
        return title_translated

    @staticmethod
    def _get_url_for_definition_language(definition, language, extension='pdf'):
        return '/plugin/mrbeam/docs/%(mrbeam_model)s/%(language)s/%(mrbeam_type)s.%(extension)s' % {
            'mrbeam_model': definition.mrbeam_model.value,
            'language': language.value,
            'mrbeam_type': definition.mrbeamdoc_type.value,
            'extension': extension}
