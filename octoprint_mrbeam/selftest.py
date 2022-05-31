from __future__ import absolute_import

import logging

import octoprint
from flask import jsonify, make_response

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.rest_handler.self_test_handler import SelfTestRestHandlerMixin


class SelfTestMixin(object, SelfTestRestHandlerMixin):
    _instance = None
    mrbeamplugin = None
    _logger = mrb_logger("octoprint.plugins.mrbeam")

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls, plugin):
        if cls._instance is None:
            cls._logger.debug('Creating new instance')
            cls._instance = cls.__new__(cls)
            cls.mrbeamplugin = plugin
            # Put any initialization here.
        return cls._instance

    # compressor tests
    def __manual_test_compressor_run_possible(self):
        # TODO return true or false if all conditions are met to run the test
        # condition operational state
        if self.mrbeamplugin._printer.is_operational():
            return True
        else:
            return False

    def __start_manual_test_compressor_run(self):
        # TODO start compressor
        if self.__manual_test_compressor_run_possible():
            self.mrbeamplugin.compressor_handler.set_compressor(100)
        else:
            return False

    def __stop_manual_test_compressor_run(self):
        # TODO stop compressor
        self.mrbeamplugin.compressor_handler.set_compressor(0)
        pass

    # airfilter tests
    def __manual_test_airfilter_fan_possible(self):
        # TODO return true or false if all conditions are met to run the test
        # condition operational state
        if self.mrbeamplugin._printer.is_operational():
            return True
        else:
            return False

    def __start_manual_test_airfilter_fan(self):
        # TODO start airfilter fan at 50%
        if self.__manual_test_airfilter_fan_possible():
            self.mrbeamplugin.dust_manager._send_fan_command(self.mrbeamplugin.dust_manager.FAN_COMMAND_ON, int(50))
        else:
            return False

    def __stop_manual_test_airfilter_fan(self):
        # TODO stop airfilter fan
        self.mrbeamplugin.dust_manager._send_fan_command(self.mrbeamplugin.dust_manager.FAN_COMMAND_ON, int(0))
        pass

    # Laser head tests
    def __manual_test_laserhead_fan_possible(self):
        # TODO return true or false if all conditions are met to run the test
        # condition operational state
        # all interlocks closed
        if self.mrbeamplugin._iobeam.is_interlock_closed() and self.mrbeamplugin._printer.is_operational():
            return True
        else:
            return False

    def __start_manual_test_laserhead_fan(self):
        # TODO move laser, activate laser, this will run the laserhead
        if self.__manual_test_laserhead_fan_possible():
            pass
        else:
            return False

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
