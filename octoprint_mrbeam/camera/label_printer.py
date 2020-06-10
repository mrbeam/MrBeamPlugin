#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import logging
import string
import datetime
import threading
from time import gmtime, strftime
if __name__ == "__main__":
	import argparse
else:
	from octoprint_mrbeam.util.device_info import get_val_from_device_info
	






class LabelPrinter(object):
	COMMAND_RLPR = 'echo "{data}" | rlpr -q -H {ip}'

	PRINTER_LINE_LEN = 78

	PRINTABLE = set(string.printable)

	def __init__(self):
		self._logger = logging.getLogger(__name__)
		self.lines = []
		self.device_label_enabled = settings().get(['printer', 'device_label_printer', 'enabled'])
		self.box_label_enabled = settings().get(['printer', 'box_label_printer', 'enabled'])
		self.report_enabled = settings().get(['printer', 'report_printer', 'enabled'])

		self._thread_print_device_label = None
		self._thread_print_box_label1 = None
		self._thread_print_box_label2 = None
		self._thread_print_ean_labels = None


	def print_or_die(self, final, results):
		if not self.device_label_enabled and not self.report_enabled: return

		if final and self.report_enabled:
			self.print_error_report(results)

		while True:
			w = WaitForBlinker([IoBeamEvents.ONEBUTTON_RELEASED], timeout=None)
			event = w.wait()
			if event == IoBeamEvents.ONEBUTTON_RELEASED:
				self._thread_print_device_label = self.run_threaded(self._thread_print_device_label, self.print_device_label)
				self._thread_print_box_label1 = self.run_threaded(self._thread_print_box_label1, self.print_box_label)
				self._thread_print_box_label2 = self.run_threaded(self._thread_print_box_label2, self.print_box_label)
				self._thread_print_ean_labels = self.run_threaded(self._thread_print_ean_labels, self.print_ean_labels)

	def run_threaded(self, my_thread, my_target):
		if my_thread is None or not my_thread.isAlive():
			my_thread = threading.Thread(target=my_target, name="printer_thread")
			my_thread.daemon = True
			my_thread.start()
		return my_thread

	def print_error_report(self, results):
		ip = settings().get(['printer', 'report_printer', 'ip'])
		linebreak = settings().get(['printer', 'report_printer', 'linebreak'])
		data = self._get_report(results, linebreak)
		self._logger.info("\n=============== error_report: start ==========================================\n%s\n=============== error_report: end   ==========================================", data)
		ok, output = self._print(ip, data)
		self._log_print_result('error_report', ok, output)
		return ok, output


	def print_device_label(self):
		ip = settings().get(['printer','device_label_printer', 'ip'])
		self._logger.info("Printing device label to %s", ip)
		zpl = self._get_zpl_device_label()
		ok, output = self._print(ip, zpl)
		self._log_print_result('device label', ok, output, zpl)
		return ok, output

	def _get_zpl_device_label(self):
		device_data = get_device_data()
		return '''
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
			^FO22,15^BQN,2,4^FDMMA{serial}^FS
			^XZ
		'''.format(name=device_data.get(DeviceDataKeys.HOSTNAME),
				   serial=device_data.get_serial_num(),
				   prod_date=Printer._get_prod_date_str())

	def print_box_label(self):
		ip = settings().get(['printer', 'box_label_printer', 'ip'])
		self._logger.info("Printing box label to %s", ip)
		zpl = self._get_zpl_box_label()
		ok, output = self._print(ip, zpl)
		self._log_print_result('box label', ok, output, zpl)
		return ok, output

	def _get_zpl_box_label(self):
		device_data = get_device_data()

		return '''
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
			^FO22,60^BQN,2,4^FDMMA{serial}^FS
			^XZ
		'''.format(name=device_data.get(DeviceDataKeys.HOSTNAME),
				   serial=device_data.get_serial_num(),
				   model=self._get_model_abbrev(),
				   prod_date=Printer._get_prod_date_str())

	def print_ean_labels(self):
		ip = settings().get(['printer', 'box_label_printer', 'ip'])
		ean = settings().get(['ean_numbers'])
		model = get_device_data().get_model()
		if model in ean and ean.get(model, None):
			for prod_string, ean_num in ean.get(model, dict()).iteritems():
				self._logger.info("Printing ean label '%s' to %s", prod_string, ip)
				zpl = self._get_zpl_ean_label(prod_string, ean_num)
				ok, output = self._print(ip, zpl)
				self._log_print_result('ean label {}'.format(prod_string), ok, output, zpl)

	def _get_zpl_ean_label(self, prod_string, ean_num):
		return '''
			^XA
			^FWN
			^FO50,20^BY4
			^BEN,140,Y,N
			^FD{ean_num}^FS
			^CF0,30
			^FO50,212^FDMr Beam II {model}^FS
			^CF0,40
			^FO270,205^FD{prod_string}^FS
			^XZ
		'''.format(prod_string=prod_string,
				   model=self._get_model_abbrev(),
				   ean_num=ean_num)


	def _get_report(self, results, linebreak="\n", print_issues_only=True):
		self.lines = []
		device_data = get_device_data()
		stick_name = settings().get(['stick', 'name'])
		# remove non-ascii chars
		if stick_name:
			stick_name = filter(lambda x: x in self.PRINTABLE, stick_name)

		self._append_line_with_head("Mrb_Check:", "v{version} |  Stick name: {stick_name}".format(version=__version__, stick_name=stick_name))
		self._append_line_with_head("Model:    ", "{model}".format(model=device_data.get_model()))
		self._append_line_with_head("Device:   ", "{hostname}, serial:{serial}".format(hostname=device_data.get(DeviceDataKeys.HOSTNAME), serial=device_data.get_serial_num()))
		# self._append_line_with_head("Laserhead:", "{laserhead}".format(laserhead=laserhead_serial_global if laserhead_serial_global is not None else ''))
		self._append_line_with_head("Time:     ", "{time}".format(time=strftime("%Y-%m-%d %H:%M:%S", gmtime())))
		self._append_line("")

		self._append_line("=============== RESULT: ======================================================")

		for r in results:
			if r.code == Result.CODE_ERROR or r.code == Result.CODE_USER_ABORT or r.code == Result.CODE_EXCEPTION:
				self._printout_result(r)
				break

		self._append_line("")
		self._append_line("=============== DETAILS: =====================================================")

		for r in results:
			if not print_issues_only or not(r.code == Result.CODE_OK or r.code == Result.CODE_SKIPPED or r.code == Result.CODE_NONE):
				self._printout_result(r)
				self._append_line("")

		# remove empty lines at the end
		while self.lines[-1:] == "":
			del(self.lines[-1:])

		out = linebreak.join(self.lines)
		# remove non-ascii chars
		out = filter(lambda x: x in self.PRINTABLE, out)
		lines = []
		return out

	def _printout_result(self, r, linebreak="\n"):
		self._append_line_with_head("Source:", r.name)
		self._append_line_with_head("{code}:".format(code=r.code), r.msg)
		for i, s in enumerate(r.solutions):
			self._append_line_with_head("Solution {num:02d}:".format(num=i+1), s)
		for m in r.metadata:
			if type(m).__name__ == 'tuple':
				self._append_line_with_head(" - {key}:".format(key=m[0]), m[1])
			else:
				self._append_line_with_head(" -", m) # an additional whitespace will be added...

	def _append_line_with_head(self, headline, body):
		line = "{head} {body}".format(head=headline, body=body)
		indentation = len(headline) + 1
		self.lines.extend(self._break_line(line, indentation, line_length=self.PRINTER_LINE_LEN))

	def _append_line(self, line):
		self.lines.extend(self._break_line(line, 0, line_length=self.PRINTER_LINE_LEN))

	def _break_line(self, line, indentation=0, line_length=-1):
		out = []
		if line_length > 0 and len(line) > line_length:
			len_full = line_length
			first = True
			while len(line) > 0:
				take = len_full if first else len_full - indentation
				l = line[:take]
				if not first:
					l = " "*indentation + l
				out.append(l)
				line = line[take:]
				first = False
		else:
			out.append(line)

		return out


	def _print(self, ip, data):
		'''
		pritns data to printer at IP using rlpr
		:param ip: printer's ip address
		:param data: data to print
		:return: Tuple (success, output): success: Boolean, output: commands STDOUT & STDERR (should be empty if successful)
		'''
		cmd = self.COMMAND_RLPR.format(ip=ip, data=data)
		out, code = exec_cmd_output(cmd, log_cmd=False)
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
		device_data = get_device_data()
		model = ""
		if device_data.get_model() in (DeviceDataModel.MRBEAM_2_DC_R1, DeviceDataModel.MRBEAM_2_DC_R2):
			model = "DCR"
		elif device_data.get_model() in (DeviceDataModel.MRBEAM_2_DC):
			model = "DC"
		return model

	# @staticmethod
	# def _get_zpl_template():
	# 	"""
	# 	Template for silver/grey labels 57x19mm
	# 	:return: String: ZPL template;
	# 	"""
	# 	return '''^XA
	# 		^FX Mr Beam Serial Label
	# 		^LS-220
	# 		^LT25
	# 		^LT25
	# 		^CF0,25
	# 		^FO135,20^FDName: {name}^FS
	# 		^CF0,20
	# 		^FO135,53^FDS/N: {serial}^FS
	# 		^FO135,80^FDProduction date: {prod_date}^FS
	# 		^FO22,15^BQN,2,4^FDMMA{serial}^FS
	# 		^XZ
	# 	'''


	@staticmethod
	def _get_prod_date_str():
		return datetime.date.today().strftime('%b %Y')


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('-n', '--name', type=str, required=True, help="Mr Beam name like 'MrBeam-XXXX'")
	parser.add_argument('-s', '--serial', type=str, required=True, help="Mr Beam serial number like '0000000009F6FD56-2F'")
	args = parser.parse_args()

	zpl = Printer._get_zpl_template().format(name=args.name, serial=args.serial, prod_date=Printer._get_prod_date_str())
	print "	"+zpl


