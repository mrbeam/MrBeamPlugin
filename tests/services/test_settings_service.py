from unittest import TestCase

from octoprint_mrbeamdoc import MrBeamModel

from octoprint_mrbeam.services.settings_service import SettingsService


class Test(TestCase):
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.service = SettingsService(LoggerMock())

    def test_get_template_settings_model_with_none_then_return_settings_empty_object(self):
        settings_model = self.service.get_template_settings_model(None)
        self._validate_empty_settings_model(settings_model)

    def test_get_template_settings_model_with_unknown_then_return_settings_empty_object(self):
        settings_model = self.service.get_template_settings_model('unknown')
        self._validate_empty_settings_model(settings_model)

    def test_get_template_settings_model_with_mrbeam2_then_return_settings_with_about_and_nonempty_documents(self):
        settings_model = self.service.get_template_settings_model(MrBeamModel.MRBEAM2.value)
        self._validate_settings_model(settings_model)

    def test_get_template_settings_model_with_dreamcut_then_return_settings_with_about_and_nonempty_documents(self):
        settings_model = self.service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)

    def _validate_empty_settings_model(self, settings_model):
        self.assertIsNotNone(settings_model)
        self.assertIsNotNone(settings_model.about)
        self.assertIsNotNone(settings_model.about.support_documents)
        self.assertEquals(settings_model.about.support_documents, [])

    def _validate_settings_model(self, settings_model):
        self.assertIsNotNone(settings_model)
        self.assertIsNotNone(settings_model.about)
        documents = settings_model.about.support_documents
        self.assertIsNotNone(documents)
        for document in documents:
            self.assertIsNotNone(document)
            self.assertIsNotNone(document.title)
            for document_link in document.document_links:
                self.assertIsNotNone(document_link)
                self.assertIsNotNone(document_link.language)
                self.assertIsNotNone(document_link.language.name)
                self.assertNotEquals(document_link.language.name, '')
                self.assertNotEquals(document_link.language.name, ' ')
                self.assertIsNotNone(document_link.language.value)
                self.assertNotEquals(document_link.language.value, '')
                self.assertNotEquals(document_link.language.value, ' ')
                self.assertIsNotNone(document_link.url)
                self.assertNotEquals(document_link.url, '')
                self.assertNotEquals(document_link.url, ' ')


class LoggerMock:
    def __init__(self):
        pass

    def comm(self, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warn(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def exception(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

    def setLevel(self, *args, **kwargs):
        pass

    def log(self, level, msg, *args, **kwargs):
        pass
