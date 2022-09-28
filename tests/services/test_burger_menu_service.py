# -*- coding: utf-8 -*-
from unittest import TestCase

from mock import patch, MagicMock
from octoprint_mrbeamdoc.enum.mrbeam_doctype import MrBeamDocType
from octoprint_mrbeamdoc.enum.mrbeam_model import MrBeamModel
from octoprint_mrbeamdoc.enum.supported_languages import SupportedLanguage
from octoprint_mrbeamdoc.model.mrbeam_doc_definition import MrBeamDocDefinition

from octoprint_mrbeam.services.document_service import DocumentService
from octoprint_mrbeam.services.burger_menu_service import BurgerMenuService
from tests.logger.test_logger import LoggerMock


class TestBurgerMenuService(TestCase):

    def setUp(self):
        super(TestBurgerMenuService, self).setUp()
        logger = LoggerMock()
        self._burger_menu_service = BurgerMenuService(logger, DocumentService(logger))

    def test_get_burger_menu_model__with_none__should_return_empty_burger_menu_model(self):
        burger_menu_model = self._burger_menu_service.get_burger_menu_model(None)
        self.assertIs(len(burger_menu_model.documents), 0)

    @patch('octoprint_mrbeam.services.burger_menu_service.get_locale')
    def test_get_burger_menu_model__with_unsupported_language__should_return_default_to_english(self, get_locale_mock):
        get_locale_mock.return_value = MagicMock(language='ch')
        burger_menu_model = self._burger_menu_service.get_burger_menu_model(MrBeamModel.MRBEAM2.value)
        self.assertIsNot(len(burger_menu_model.documents), 0)
        for document in burger_menu_model.documents:
            self.assertEquals(document.document_link.language, SupportedLanguage.ENGLISH)

    @patch('octoprint_mrbeam.services.burger_menu_service.MrBeamDocUtils.get_mrbeam_definitions_for')
    @patch('octoprint_mrbeam.services.burger_menu_service.get_locale')
    def test_get_burger_menu_model__with_language_not_valid_for_definition__should_fallback_to_english(self,
                                                                                                       get_locale_mock,
                                                                                                       get_mrbeam_definitions_for_mock):
        get_locale_mock.return_value = MagicMock(language='de')
        MOCK_DEFINITION = MrBeamDocDefinition(MrBeamDocType.QUICKSTART_GUIDE, MrBeamModel.MRBEAM2,
                                              [SupportedLanguage.ENGLISH])
        get_mrbeam_definitions_for_mock.return_value = [MOCK_DEFINITION]
        burger_menu_model = self._burger_menu_service.get_burger_menu_model(MrBeamModel.MRBEAM2.value)
        self.assertIsNot(len(burger_menu_model.documents), 0)
        for document in burger_menu_model.documents:
            self.assertEquals(document.document_link.language, SupportedLanguage.ENGLISH)

    @patch('octoprint_mrbeam.services.burger_menu_service.get_locale')
    def test_get_burger_menu_model__with_supported_language__should_return_documents_in_that_language(self,
                                                                                                      get_locale_mock):
        get_locale_mock.return_value = MagicMock(language='de')
        burger_menu_model = self._burger_menu_service.get_burger_menu_model(MrBeamModel.MRBEAM2.value)
        self.assertIsNot(len(burger_menu_model.documents), 0)
        for document in burger_menu_model.documents:
            self.assertEquals(document.document_link.language, SupportedLanguage.GERMAN)

    @patch('octoprint_mrbeam.services.burger_menu_service.MrBeamDocUtils.get_mrbeam_definitions_for')
    @patch('octoprint_mrbeam.services.document_service.gettext')
    @patch('octoprint_mrbeam.services.burger_menu_service.get_locale')
    def test_get_burger_menu_model__with_unicode_translation__should_work(self, get_locale_mock, get_text_mock,
                                                                          get_mrbeam_definitions_for_mock):
        get_locale_mock.return_value = MagicMock(language='es')
        get_text_mock.return_value = u'Guía de usuário äëïöü l\'ecole très Garçon sûr'
        MOCK_DEFINITION = MrBeamDocDefinition(MrBeamDocType.USER_MANUAL, MrBeamModel.MRBEAM2,
                                              [SupportedLanguage.ENGLISH, SupportedLanguage.SPANISH])
        get_mrbeam_definitions_for_mock.return_value = [MOCK_DEFINITION]
        burger_menu_model = self._burger_menu_service.get_burger_menu_model(MrBeamModel.MRBEAM2.value)
        self.assertIsNot(len(burger_menu_model.documents), 0)
        for document in burger_menu_model.documents:
            self.assertEquals(document.document_link.language, SupportedLanguage.SPANISH)

    @patch('octoprint_mrbeam.services.burger_menu_service.MrBeamDocUtils.get_mrbeam_definitions_for')
    @patch('octoprint_mrbeam.services.document_service.gettext')
    @patch('octoprint_mrbeam.services.burger_menu_service.get_locale')
    def test_get_burger_menu_model__with_null_translation__should_not_crash_and_return_title_as_None(self,
                                                                                                     get_locale_mock,
                                                                                                     get_text_mock,
                                                                                                     get_mrbeam_definitions_for_mock):
        get_locale_mock.return_value = MagicMock(language='es')
        get_text_mock.return_value = None
        MOCK_DEFINITION = MrBeamDocDefinition(MrBeamDocType.USER_MANUAL, MrBeamModel.MRBEAM2,
                                              [SupportedLanguage.ENGLISH, SupportedLanguage.SPANISH])
        get_mrbeam_definitions_for_mock.return_value = [MOCK_DEFINITION]
        burger_menu_model = self._burger_menu_service.get_burger_menu_model(MrBeamModel.MRBEAM2.value)
        self.assertIsNot(len(burger_menu_model.documents), 0)
        for document in burger_menu_model.documents:
            self.assertEquals(document.document_link.language, SupportedLanguage.SPANISH)
            self.assertEquals(document.title, None)
