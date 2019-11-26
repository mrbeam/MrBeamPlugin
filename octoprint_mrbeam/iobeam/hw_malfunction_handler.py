from flask.ext.babel import gettext

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None


def hwMalfunctionHandler(plugin):
	global _instance
	if _instance is None:
		_instance = HwMalfunctionHandler(plugin)
	return _instance


class HwMalfunctionHandler(object):
	BOTTOM_OPEN_ID = 'bottom_open'

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.hw_malfunction")
		self._plugin = plugin
		self._settings = plugin._settings
		self._event_bus = plugin._event_bus
		self._shown_messages = []

		self.hardware_malfunction = False
		self.hardware_malfunction_notified = False

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._analytics_handler = self._plugin.analytics_handler
		self._iobeam_handler = self._plugin.iobeam

	def hw_malfunction_procedure(self, dataset):
		show_notification = False
		self._logger.warn("hardware_malfunction: %s", dataset)

		for id, data in dataset.items():
			data = data or {}
			msg = data.get('msg', id)
			self._plugin.fire_event(MrBeamEvents.HARDWARE_MALFUNCTION, dict(id=id, msg=msg, data=data))  # todo iratxe: we need to stop the laser job

			if id == self.BOTTOM_OPEN_ID:
				self.send_bottom_open_frontend_notification()
			else:
				if msg not in self._shown_messages:
					show_notification = True
					self._shown_messages.append(msg)

		if show_notification:
			self.send_hardware_malfunction_frontend_notification()

		self._analytics_handler.add_iobeam_message_log(self._iobeam_handler.iobeam_version, dataset)

	# todo iratxe: should we unify the different malfunctions? (including compressor errors in hardware_malfunction)
	def report_hw_malfunction(self):
		self._plugin.fire_event(MrBeamEvents.HARDWARE_MALFUNCTION, dict(id=id_str, msg=msg, data=data))
		self._analytics_handler.add_iobeam_message_log(self._iobeam_handler.iobeam_version, dataset)

	def send_hardware_malfunction_frontend_notification(self, *args, **kwargs):
		if self._shown_messages:  # todo iratxe
			user_msg = "<br/>".join(self._shown_messages)
			# if user_msg not in self.reported_hardware_malfunctions:
			# self.reported_hardware_malfunctions.append(user_msg)
			text = '<br/>' + gettext(
				"A possible hardware malfunction has been detected on this device. Please contact our support team immediately at:") + \
				'<br/><a href="https://mr-beam.org/ticket" target="_blank">mr-beam.org/ticket</a><br/><br/>' \
				'<strong>' + gettext("Error:") + '</strong><br/>{}'.format(user_msg)
			self._plugin.notify_frontend(
				title=gettext("Hardware malfunction"),
				text=text,
				type="error",
				sticky=True,
			)

	def send_possible_hardware_malfunction_frontend_notification(self, dataset):
		text = '<br/>' + gettext(
			"A possible hardware malfunction has been detected on this device. Please contact our support team immediately at:") + \
			'<br/><a href="https://mr-beam.org/support" target="_blank">mr-beam.org/support</a><br/><br/>' \
			'<strong>' + gettext("Error:") + '</strong><br/>{}'.format(dataset)
		self._plugin.notify_frontend(
			title=gettext("Hardware malfunction"),
			text=text,
			type="error",
			sticky=True,
			replay_when_new_client_connects=True
		)

	def send_bottom_open_frontend_notification(self):
		text = '<br/>' + gettext(
			"The bottom plate is not closed correctly. "
			"Please make sure that the bottom is correctly mounted as described in the Mr Beam II user manual.")
		self._plugin.notify_frontend(
			title=gettext("Bottom Plate Error"),
			text=text,
			type="error",
			sticky=True,
			replay_when_new_client_connects=True
		)
