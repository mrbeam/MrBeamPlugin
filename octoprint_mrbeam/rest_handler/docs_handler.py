from flask import abort, send_file

import octoprint.plugin
from octoprint_mrbeamdoc import get_doc_path, MrBeamDocType, MrBeamModel, SupportedLanguage, MrBeamDocNotFoundException


class DocsRestHandlerMixin:
    @octoprint.plugin.BlueprintPlugin.route(
        "/docs/<string:model>/<string:language>/<string:doctype>.<string:extension>", methods=["GET"])
    def get_doc(self, model, doctype, language, extension):
        self._logger.debug(
            'Request to Model: %(model)s Doctype: %(doctype)s Language: %(language)s Extension:%(extension)s',
            {'model': model, 'doctype': doctype, 'language': language, 'extension': extension})

        mrbeam_model_found = next(
            (mrbea_model for mrbea_model in MrBeamModel if mrbea_model.value.lower() == model.lower()), None)
        supported_language_found = next((supported_language for supported_language in SupportedLanguage if
                                         supported_language.value.lower() == language.lower()), None)
        mrbeam_doctype_found = next(
            (mrbea_doctype for mrbea_doctype in MrBeamDocType if mrbea_doctype.value.lower() == doctype.lower()), None)

        if mrbeam_model_found is None or supported_language_found is None or mrbeam_doctype_found is None:
            abort(404)

        try:
            mrbeamdoc = get_doc_path(mrbeam_doctype_found, mrbeam_model_found, supported_language_found,
                                     extension=extension)
        except MrBeamDocNotFoundException as e:
            self._logger.warn(e)
            abort(404)

        return send_file(mrbeamdoc.get_file_reference(), attachment_filename=mrbeamdoc.get_file_name_with_extension())
