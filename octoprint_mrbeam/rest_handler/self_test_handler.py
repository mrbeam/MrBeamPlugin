from __future__ import absolute_import

import octoprint.plugin
from flask import abort, send_file, jsonify, make_response
from octoprint_mrbeamdoc.exception.mrbeam_doc_not_found import MrBeamDocNotFoundException
from octoprint_mrbeamdoc.utils.mrbeam_doc_utils import MrBeamDocUtils

# from octoprint_mrbeam.selftest import SelfTestMixin


class SelfTestRestHandlerMixin:
    """
    This class contains all the rest handlers and endpoints related to handle docs
    """

    @octoprint.plugin.BlueprintPlugin.route(
        "/self_test_fan", methods=["GET"])
    def can_self_test_fan(self):
        # self._logger.debug(
        #     'Request to Model: %(model)s Doctype: %(doctype)s Language: %(language)s Extension:%(extension)s',
        #     {'model': model, 'doctype': doctype, 'language': language, 'extension': extension})

        # try:
        #     mrbeamdoc = MrBeamDocUtils.get_mrbeamdoc_for(mrbeam_doctype_found, mrbeam_model_found,
        #                                                  supported_language_found, extension=extension)
        # except MrBeamDocNotFoundException as e:
        #     self._logger.warn(e)
        #     abort(404)
        #
        # return send_file(mrbeamdoc.get_file_reference(), attachment_filename=mrbeamdoc.get_file_name_with_extension())
        self._logger.debug(
            'test self test fan')
        self._logger.debug(
            'test {}'.format(self.__manual_test_compressor_run_possible()))
        return jsonify(self.__manual_test_compressor_run_possible())

    @octoprint.plugin.BlueprintPlugin.route(
        "/test", methods=["GET"])
    def test(self):
        self._logger.debug(
            'test called')
        # self._logger.debug(
        #     'Request to Model: %(model)s Doctype: %(doctype)s Language: %(language)s Extension:%(extension)s',
        #     {'model': model, 'doctype': doctype, 'language': language, 'extension': extension})

        # try:
        #     mrbeamdoc = MrBeamDocUtils.get_mrbeamdoc_for(mrbeam_doctype_found, mrbeam_model_found,
        #                                                  supported_language_found, extension=extension)
        # except MrBeamDocNotFoundException as e:
        #     self._logger.warn(e)
        #     abort(404)
        #
        # return send_file(mrbeamdoc.get_file_reference(), attachment_filename=mrbeamdoc.get_file_name_with_extension())
        return make_response("bla", 400)