from flask_babel import get_locale

from octoprint_mrbeam.decorator.catch_import_error import prevent_execution_on_import_error
from octoprint_mrbeam.model import EmptyImport

try:
    from octoprint_mrbeamdoc.enum.supported_languages import SupportedLanguage
    from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils
except ImportError:
    MrBeamDocUtils = EmptyImport("from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils")
    SupportedLanguage = EmptyImport("from octoprint_mrbeamdoc.enum.supported_languages import SupportedLanguage")

from octoprint_mrbeam.model.burger_menu_model import BurgerMenuModel


class BurgerMenuService:
    """
    In this class we gather all the service layer calculations needed regarding the burger menu
    """

    def __init__(self, logger, document_service):
        self._logger = logger
        self._document_service = document_service

    @prevent_execution_on_import_error(MrBeamDocUtils, default_return=BurgerMenuModel())
    def get_burger_menu_model(self, mrbeam_model):
        """
        mrbeam_model String: Name of the running mrbeam_model

        Return BurgerMenuModel containing all the burger menu related information for this specific mrbeam_model
        """
        mrbeam_model_found = MrBeamDocUtils.get_mrbeam_model_enum_for(mrbeam_model)
        if mrbeam_model_found is None:
            self._logger.error('MrBeamModel not identified %s', mrbeam_model)
            return BurgerMenuModel()

        language_found = MrBeamDocUtils.get_supported_language_enum_for(get_locale().language)
        if language_found is None:
            language_found = SupportedLanguage.ENGLISH

        burger_model = BurgerMenuModel()
        definitions = MrBeamDocUtils.get_mrbeam_definitions_for(mrbeam_model_found)
        for definition in definitions:
            language_found = language_found if definition.is_language_supported(
                language_found) else SupportedLanguage.ENGLISH
            document_simple = self._document_service.get_document_simple_for(definition, language_found)
            burger_model.add_document(document_simple)
        return burger_model
