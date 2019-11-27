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
		self._event_bus = plugin._event_bus

		self._messages_to_show = []
		self.hardware_malfunction = False

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._analytics_handler = self._plugin.analytics_handler
		self._iobeam_handler = self._plugin.iobeam

	def report_hw_malfunction_from_plugin(self, malfunction_id, msg, payload=None):
		if payload is None:
			payload = {}

		data = dict(
			msg=msg,
			payload=payload,
		)

		dataset = dict(
			id=malfunction_id,
			data=data,
		)

		self.report_hw_malfunction(dataset, from_plugin=True)

	def report_hw_malfunction(self, dataset, from_plugin=False):
		self.hardware_malfunction = True
		self._logger.warn("hardware_malfunction: %s", dataset)

		new_msg = False
		bottom_open = False
		for malfunction_id, data in dataset.items():
			data = data or {}
			msg = data.get('msg', malfunction_id)
			self._plugin.fire_event(MrBeamEvents.HARDWARE_MALFUNCTION, dict(id=malfunction_id, msg=msg, data=data))

			if malfunction_id == self.BOTTOM_OPEN_ID:
				bottom_open = True
			else:
				if msg not in self._messages_to_show:
					new_msg = True
					self._messages_to_show.append(msg)

		self._notify_user_about_malfunction(new_msg, bottom_open)
		self._analytics_handler.add_iobeam_message_log(self._iobeam_handler.iobeam_version, dataset, from_plugin)

	def _notify_user_about_malfunction(self, new_msg=None, bottom_open=None):
		if new_msg:
			self.show_hw_malfunction_notification()

		if bottom_open:
			self.show_bottom_open_notification()

	def show_hw_malfunction_notification(self, dataset=None):
		if dataset:
			message = dataset
		elif self._messages_to_show:
			message = "<br/>".join(self._messages_to_show)
		else:
			message = None

		if message:
			text = '<br/>' + gettext(
				'A possible hardware malfunction has been detected on this device. Please contact our support team immediately at:') + \
				'<br/><a href="https://mr-beam.org/support" target="_blank">mr-beam.org/support</a><br/><br/>' \
				'<strong>' + gettext("Error:") + '</strong><br/>{}'.format(message)
			self._plugin.notify_frontend(
				title=gettext("Hardware malfunction"),
				text=text,
				type="error",
				sticky=True,
				replay_when_new_client_connects=True
			)

	def show_bottom_open_notification(self):
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
