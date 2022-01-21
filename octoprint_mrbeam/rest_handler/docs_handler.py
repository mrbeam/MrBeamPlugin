import octoprint.plugin
from flask import abort, send_file
from octoprint_mrbeamdoc.enum.mrbeam_doctype import MrBeamDocType
from octoprint_mrbeamdoc.enum.mrbeam_model import MrBeamModel
from octoprint_mrbeamdoc.enum.supported_languages import SupportedLanguage
from octoprint_mrbeamdoc.exception.mrbeam_doc_not_found import MrBeamDocNotFoundException
from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils


class DocsRestHandlerMixin:
    """
    This class contains all the rest handlers and endpoints related to handle docs
    """

    @octoprint.plugin.BlueprintPlugin.route(
        "/docs/<string:model>/<string:language>/<string:doctype>.<string:extension>", methods=["GET"])
    def get_doc(self, model, doctype, language, extension):
        self._logger.debug(
            'Request to Model: %(model)s Doctype: %(doctype)s Language: %(language)s Extension:%(extension)s',
            {'model': model, 'doctype': doctype, 'language': language, 'extension': extension})

        mrbeam_model_found = next(
            (mrbeam_model for mrbeam_model in MrBeamModel if mrbeam_model.value.lower() == model.lower()), None)
        supported_language_found = next((supported_language for supported_language in SupportedLanguage if
                                         supported_language.value.lower() == language.lower()), None)
        mrbeam_doctype_found = next(
            (mrbeam_doctype for mrbeam_doctype in MrBeamDocType if mrbeam_doctype.value.lower() == doctype.lower()),
            None)

        if mrbeam_model_found is None or supported_language_found is None or mrbeam_doctype_found is None:
            abort(404)

        try:
            mrbeamdoc = MrBeamDocUtils.get_mrbeamdoc_for(mrbeam_doctype_found, mrbeam_model_found,
                                                        supported_language_found, extension=extension)
        except MrBeamDocNotFoundException as e:
            self._logger.warn(e)
            abort(404)

        return send_file(mrbeamdoc.get_file_reference(), attachment_filename=mrbeamdoc.get_file_name_with_extension())
