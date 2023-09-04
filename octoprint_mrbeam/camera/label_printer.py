#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import datetime
from octoprint.server.util.flask import get_json_command_from_request
from octoprint_mrbeam.util.device_info import (
    deviceInfo,
    MODEL_MRBEAM_2_DC_S,
    MODEL_MRBEAM_2_DC_R1,
    MODEL_MRBEAM_2_DC_R2,
    MODEL_MRBEAM_2_DC,
    MODEL_MRBEAM_2_DC_X,
)
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd_output
from octoprint_mrbeam.mrbeam_events import MrBeamEvents


_instance = None


def labelPrinter(plugin, use_dummy_values=False):
    # This method is being used by the camera plugin
    # Do not modify without checking the usage in the camera plugin

    global _instance
    if _instance is None:
        _instance = LabelPrinter(plugin, use_dummy_values=use_dummy_values)
    return _instance


class LabelPrinter(object):
    COMMAND_RLPR = 'echo "{data}" | rlpr -q -H {ip}'

    PRINTER = dict(
        device_label_printer=dict(enabled=True, ip="192.168.1.201"),
        box_label_printer=dict(enabled=True, ip="192.168.1.202"),
    )
    EAN_NUMBERS = dict(
        MRBEAM2=None,
        MRBEAM2_DC_R1=None,
        MRBEAM2_DC_R2=None,
        MRBEAM2_DC=dict(single="4260625360156", bundle="4260625360163"),
        MRBEAM2_DC_S=dict(single="4260625361023", bundle="4260625361030"),
        MRBEAM2_DC_X=dict(single="4260625362136", bundle="4260625362143"),
    )

    def __init__(self, plugin, use_dummy_values=False):
        self._plugin = plugin
        self._logger = mrb_logger("octoprint.plugins.mrbeam.camera.label_printer")
        self._device_info = deviceInfo(use_dummy_values=use_dummy_values)

    def print_label(self, request):
        valid_commands = {"print_label": ["labelType"]}
        command, data, response = get_json_command_from_request(request, valid_commands)
        if response is not None:
            return response

        label_type = data.get("labelType", None)
        blink = data.get("blink", None)

        ok, out = None, None
        if label_type == "deviceLabel":
            ok, out = self.print_serial_label()
        elif label_type == "boxLabel":
            ok, out = self.print_box_label()
        elif label_type == "eanLabel":
            ok, out = self.print_ean_labels()
        elif label_type is None:
            ok = True
        else:
            ok = False
            out = "Unknown label: {}".format(label_type)
            self._logger.debug("printLabel() unknown labelType: %s ", label_type)

        if ok and blink:
            self._plugin._event_bus.fire(MrBeamEvents.BLINK_PRINT_LABELS)
        elif blink is False:
            self._plugin._event_bus.fire(MrBeamEvents.LENS_CALIB_DONE)

        res = dict(
            labelType=label_type,
            success=ok,
            error=out,
        )

        return res

    def print_serial_label(self):
        try:
            ip = self.PRINTER["device_label_printer"]["ip"]
            self._logger.info("Printing device label to %s", ip)
            zpl = self._get_zpl_device_label()
            ok, output = self._print(ip, zpl)
            self._log_print_result("device label", ok, output, zpl)
            return ok, output
        except:
            self._logger.exception("Exception is _print_device_label()")

    def _get_zpl_device_label(self):
        return """
			^XA
			^FX Mr Beam Serial Label
			^LS-220
			^LT25
			^LT25
			^CF0,25
			^FO135,20^FDName: {name}^FS
			^CF0,20
			^FO135,53^FDS/N: {serial}^FS
			^FO135,80^FDProduction date: {prod_date}^FS
			^FO22,15^BQN,2,4^FDMMA {serial}^FS
			^XZ
		""".format(
            name=self._device_info.get_hostname(),
            serial=self._device_info.get_serial(),
            prod_date=self._get_production_date_formatted(),
        )

    def print_box_label(self):
        try:
            ip = self.PRINTER["box_label_printer"]["ip"]
            self._logger.info("Printing box label to %s", ip)
            zpl = self._get_zpl_box_label()
            ok, output = self._print(ip, zpl)
            self._log_print_result("box label", ok, output, zpl)
            return ok, output
        except:
            self._logger.exception("Exception is _print_box_label()")

    def _get_zpl_box_label(self):
        return """
			^XA
			^FX Mr Beam box Label
			^LS0
			^LT40
			^CF0,40
			^FO20,20^FDMr Beam II {model}^FS
			^CF0,25
			^FO135,85^FDName: {name}^FS
			^CF0,30
			^FO20,180^FDS/N: {serial}^FS
			^CF0,35
			^FO135,125^FD{prod_date}^FS
			^FO22,60^BQN,2,4^FDMMA {serial}^FS
			^XZ
		""".format(
            name=self._device_info.get_hostname(),
            serial=self._device_info.get_serial(),
            model=self._get_model_abbrev(),
            prod_date=self._get_production_date_formatted(),
        )

    def print_ean_labels(self):
        try:
            ip = self.PRINTER["box_label_printer"]["ip"]
            model = self._device_info.get_model()
            ok = True
            out = []
            if self.EAN_NUMBERS.get(model, None):
                for prod_string, ean_num in self.EAN_NUMBERS.get(
                    model, dict()
                ).iteritems():
                    self._logger.info("Printing ean label '%s' to %s", prod_string, ip)
                    zpl = self._get_zpl_ean_label(prod_string, ean_num)
                    _ok, _output = self._print(ip, zpl)
                    self._log_print_result(
                        "ean label {}".format(prod_string), _ok, _output, zpl
                    )
                    ok = ok and _ok
                    out.append("ean label 2: '{}'".format(_output))
            else:
                ok = False
                out.append("No EAN numbers for model {}".format(model))
            return ok, " | ".join(out)
        except:
            self._logger.exception("Exception is _print_ean_labels()")

    def _get_zpl_ean_label(self, prod_string, ean_num):
        return """
			^XA
			^FWN
			^FO40,20^BY3
			^BEN,100,Y,N
			^FD{ean_num}^FS
			^CF0,30
			^FO10,180^FDMr Beam II {model}^FS
			^CF0,45
			^FO240,168^FD{prod_string}^FS
			^XZ
		""".format(
            prod_string=prod_string, model=self._get_model_abbrev(), ean_num=ean_num
        )

    def _print(self, ip, data):
        """pritns data to printer at IP using rlpr.

        :param ip: printer's ip address
        :param data: data to print
        :return: Tuple (success, output): success: Boolean, output: commands STDOUT & STDERR (should be empty if successful)
        """
        cmd = self.COMMAND_RLPR.format(ip=ip, data=data)
        out, code = exec_cmd_output(cmd, log=False, shell=True)
        return (code == 0), out

    def _log_print_result(self, name, ok, output, payload=None):
        msg = "Print of {}: ok:{}, output: '{}'".format(name, ok, output)
        if payload:
            msg = "{}\n{}".format(msg, payload)
        if ok:
            self._logger.info(msg)
        else:
            self._logger.warn(msg)

    def _get_model_abbrev(self):
        model = ""
        if self._device_info.get_model() in (
            MODEL_MRBEAM_2_DC_R1,
            MODEL_MRBEAM_2_DC_R2,
        ):
            model = "DCR"
        elif self._device_info.get_model() == MODEL_MRBEAM_2_DC:
            model = "DC"
        elif self._device_info.get_model() == MODEL_MRBEAM_2_DC_S:
            model = "DC [S]"
        elif self._device_info.get_model() == MODEL_MRBEAM_2_DC_X:
            model = "DC [x]"
        return model

    def _get_production_date_formatted(self):
        """
        Converts production_date from "2020-06-10" to "Jun 2020"
        :return:
        """
        prod_date_str = self._device_info.get_production_date()
        if prod_date_str is None:
            return ""
        else:
            prod_date_str = prod_date_str[:10]
            return datetime.datetime.strptime(prod_date_str, "%Y-%m-%d").strftime(
                "%b %Y"
            )
