from unittest import TestCase

import requests
import yaml
from mock import patch
from octoprint.plugin import PluginSettings
from octoprint.settings import Settings
from octoprint_mrbeamdoc.enum.mrbeam_model import MrBeamModel

from octoprint_mrbeam import DocumentService, SWUpdateTier
from octoprint_mrbeam.services import settings_service
from octoprint_mrbeam.services.settings_service import SettingsService
from tests.logger.test_logger import LoggerMock


class TestSettingsService(TestCase):
    def setUp(self):
        super(TestSettingsService, self).setUp()
        logger = LoggerMock()
        self._settings_service = SettingsService(logger, DocumentService(logger))

    def test_get_template_settings_model_with_none__then_return_settings_empty_object(self):
        settings_model = self._settings_service.get_template_settings_model(None)
        self._validate_empty_settings_model(settings_model)

    def test_get_template_settings_model_with_unknown__then_return_settings_empty_object(self):
        settings_model = self._settings_service.get_template_settings_model('unknown')
        self._validate_empty_settings_model(settings_model)

    def test_get_template_settings_model_with_mrbeam2__then_return_settings_with_about_and_nonempty_documents(self):
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.MRBEAM2.value)
        self._validate_settings_model(settings_model)

    def test_get_template_settings_model_with_dreamcut__then_return_settings_with_about_and_nonempty_documents(self):
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get',
           side_effect=requests.exceptions.RequestException())
    def test_get_template_settings_model_with_no_internet__then_return_settings_with_empty_material_store_settings(
            self, requests_mock):
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load', side_effect=yaml.YAMLError())
    def test_get_template_settings_model_with_yaml_issue_in_material_store__then_empty_material_store_settings(
            self, yaml_mock, requests_mock):
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_none_material_store_settings__then_empty_material_store_settings(self,
                                                                                                               yaml_mock, requests_mock):
        yaml_mock.return_value = None
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_empty_material_store_settings__then_empty_material_store_settings(self,
                                                                                                                yaml_mock, requests_mock):
        yaml_mock.return_value = {}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_no_material_store_settings__then_empty_material_store_settings(self,
                                                                                                             yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_no_environment_material_store_settings__then_empty_material_store_settings(
            self, yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {'environment': {}}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_no_matching_environment_material_store_settings__then_empty_material_store_settings(
            self, yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {
            'environment': {'doesnotexist': {'url': 'https://test.material.store.mr-beam.org', 'enabled': True, 'healthcheck_url': 'https://test.material.store.mr-beam.org/api/healthcheck'}}}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_no_url_material_store_settings__then_empty_material_store_settings(self,
                                                                                                                 yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {
            'environment': {'prod': {'enabled': True, 'healthcheck_url': 'https://test.material.store.mr-beam.org/api/healthcheck'}}}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_no_enabled_material_store_settings__then_empty_material_store_settings(
            self, yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {
            'environment': {'prod': {'url': 'https://test.material.store.mr-beam.org', 'healthcheck_url': 'https://test.material.store.mr-beam.org/api/healthcheck'}}}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_no_healthcheck_url_material_store_settings__then_empty_material_store_settings(
            self, yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {
            'environment': {'prod': {'enabled': True, 'url': 'https://test.material.store.mr-beam.org'}}}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self._validate_empty_material_store_settings(settings_model)

    @patch('octoprint_mrbeam.services.settings_service.requests.get')
    @patch('octoprint_mrbeam.services.settings_service.yaml.load')
    def test_get_template_settings_model_with_correct_material_store_settings__then_valid_settings(self, yaml_mock, requests_mock):
        yaml_mock.return_value = {'material-store': {
            'environment': {'prod': {'url': 'https://test.material.store.mr-beam.org', 'enabled': True, 'healthcheck_url': 'https://test.material.store.mr-beam.org/api/healthcheck'}}}}
        settings_model = self._settings_service.get_template_settings_model(MrBeamModel.DREAMCUT_S.value)
        self._validate_settings_model(settings_model)
        self.assertEquals(settings_model.material_store.url, 'https://test.material.store.mr-beam.org')
        self.assertEquals(settings_model.material_store.enabled, True)
        self.assertEquals(settings_model.material_store.healthcheck_url, 'https://test.material.store.mr-beam.org/api/healthcheck')

    def test_get_environment_from_settings_with_none__then_stable(self):
        environment = settings_service.get_environment_enum_from_plugin_settings(None)
        self.assertEquals(environment, SWUpdateTier.STABLE)

    def test_get_environment_from_settings_with_empty_plugin_settings__then_stable(self):
        settings = PluginSettings(Settings(), 'mrbeam-test-plugin')
        environment = settings_service.get_environment_enum_from_plugin_settings(settings)
        self.assertEquals(environment, SWUpdateTier.STABLE)

    def test_get_environment_from_settings_with_none_dev__then_stable(self):
        plugin_settings = PluginSettings(Settings(), 'mrbeam-test-plugin')
        plugin_settings.set(['dev'], None, force=True)
        environment = settings_service.get_environment_enum_from_plugin_settings(plugin_settings)
        self.assertEquals(environment, SWUpdateTier.STABLE)

    def test_get_environment_from_settings_with_none_software_tier__then_stable(self):
        plugin_settings = PluginSettings(Settings(), 'mrbeam-test-plugin')
        plugin_settings.set(['dev', 'software_tier'], None, force=True)
        environment = settings_service.get_environment_enum_from_plugin_settings(plugin_settings)
        self.assertEquals(environment, SWUpdateTier.STABLE)

    def test_get_environment_from_settings_with_beta_lower_software_tier__then_beta(self):
        plugin_settings = PluginSettings(Settings(), 'mrbeam-test-plugin')
        plugin_settings.set(['dev', 'software_tier'], 'beta', force=True)
        environment = settings_service.get_environment_enum_from_plugin_settings(plugin_settings)
        self.assertEquals(environment, SWUpdateTier.BETA)

    def test_get_environment_from_settings_with_alpha_upper_software_tier__then_beta(self):
        plugin_settings = PluginSettings(Settings(), 'mrbeam-test-plugin')
        plugin_settings.set(['dev', 'software_tier'], 'ALPHA', force=True)
        environment = settings_service.get_environment_enum_from_plugin_settings(plugin_settings)
        self.assertEquals(environment, SWUpdateTier.ALPHA)

    def _validate_empty_settings_model(self, settings_model):
        self.assertIsNotNone(settings_model)
        self.assertIsNotNone(settings_model.about)
        self.assertIsNotNone(settings_model.about.support_documents)
        self.assertEqual(settings_model.about.support_documents, [])

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
                self.assertNotEqual(document_link.language.name, '')
                self.assertNotEqual(document_link.language.name, ' ')
                self.assertIsNotNone(document_link.language.value)
                self.assertNotEqual(document_link.language.value, '')
                self.assertNotEqual(document_link.language.value, ' ')
                self.assertIsNotNone(document_link.url)
                self.assertNotEqual(document_link.url, '')
                self.assertNotEqual(document_link.url, ' ')

    def _validate_empty_material_store_settings(self, settings_model):
        self.assertIsNotNone(settings_model)
        self.assertIsNotNone(settings_model.material_store)
        self.assertIsNotNone(settings_model.material_store.enabled)
        self.assertIsNotNone(settings_model.material_store.url)
        self.assertIsNotNone(settings_model.material_store.healthcheck_url)
        self.assertEquals(settings_model.material_store.enabled, False)
        self.assertEquals(settings_model.material_store.url, "")
        self.assertEquals(settings_model.material_store.healthcheck_url, "")
