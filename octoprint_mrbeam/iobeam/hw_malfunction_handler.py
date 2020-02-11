# coding=utf-8


import threading
import urllib

from flask.ext.babel import gettext

from octoprint.events import Events as OctoPrintEvents
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
	MALFUNCTION_ID_BOTTOM_OPEN =            'bottom_open'
	MALFUNCTION_ID_LASERHEADUNIT_MISSING =  'laserheadunit_missing'
	MALFUNCTION_ID_GENERAL =                'hw_malfunction'

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.hw_malfunction")
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._printer = plugin._printer

		self._messages_to_show = {}
		self._timer = None
		self.hardware_malfunction = False

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._analytics_handler = self._plugin.analytics_handler
		self._iobeam_handler = self._plugin.iobeam

	def report_hw_malfunction_from_plugin(self, malfunction_id, msg, payload=None):
		if not isinstance(payload, dict):
			payload = {}
		data = dict(
			msg=msg,
			payload=payload,
		)
		dataset = {
			malfunction_id: data
		}

		self.report_hw_malfunction(dataset, from_plugin=True)

	def report_hw_malfunction(self, dataset, from_plugin=False):
		self.hardware_malfunction = True
		self._logger.warn("hardware_malfunction: %s", dataset)
		for malfunction_id, data in dataset.items():
			data = data or {}
			msg = data.get('msg', malfunction_id)
			data['msg'] = msg
			self._messages_to_show[malfunction_id] = data
			self._plugin.fire_event(MrBeamEvents.HARDWARE_MALFUNCTION, dict(id=malfunction_id, msg=msg, data=data))

		self._analytics_handler.add_iobeam_message_log(self._iobeam_handler.iobeam_version, dataset, from_plugin=from_plugin)
		self._start_notification_timer()

	def _start_notification_timer(self):
		if self._timer is not None:
			self._timer.cancel()
		self._timer = threading.Timer(1.0, self.show_hw_malfunction_notification)
		self._timer.start()

	def show_hw_malfunction_notification(self, force=False):
		notifications = []
		general_malfunctions = []
		for malfunction_id, data in self._messages_to_show.items():
			if malfunction_id == self.MALFUNCTION_ID_BOTTOM_OPEN:
				notifications.append(self._get_notification_bottom_open())
			elif malfunction_id == self.MALFUNCTION_ID_LASERHEADUNIT_MISSING:
				notifications.append(self._get_notification_leaserheadunit_missing(data.get('msg', None)))
			else:
				general_malfunctions.append(data.get('msg', None))

		if general_malfunctions:
			notifications.append(self._get_notification_hardware_malfunction(general_malfunctions))

		for n in notifications:
			n['force'] = force
			self._plugin.notify_frontend(**n)

	def _get_notification_bottom_open(self):
		text = '<br/>' + gettext(
			"The bottom plate is not closed correctly. "
			"Please make sure that the bottom is correctly mounted as described in the Mr Beam II user manual.") + \
			self._get_knowledgebase_link(url='https://mr-beam.freshdesk.com/support/solutions/articles/43000557280')
		return dict(
			title=gettext("Bottom Plate Error"),
			text=text,
			type="error",
			sticky=True,
			replay_when_new_client_connects=True
		)

	def _get_notification_leaserheadunit_missing(self, msg):
		text = '<br/>' + gettext(
			"Laser head unit not found. "
			"Please make sure that the laser head unit is connected correctly.") + \
			self._get_knowledgebase_link(url='https://mr-beam.freshdesk.com/support/solutions/articles/43000557279') + \
			self._get_error_text(msg)
		return dict(
			title=gettext("No laser head unit found"),
			text=text,
			type="error",
			sticky=True,
			replay_when_new_client_connects=True
		)

	def _get_notification_hardware_malfunction(self, msgs=[]):
		text = '<br/>' + gettext(
			'A possible hardware malfunction has been detected on this device. Please contact our support team immediately at:') + \
			self._get_knowledgebase_link(url='https://mr-beam.freshdesk.com/support/solutions/articles/43000557281') + \
			self._get_error_text(msgs)
		return dict(
			title=gettext("Hardware malfunction"),
			text=text,
			type="error",
			sticky=True,
			replay_when_new_client_connects=True,
		)

	def _get_knowledgebase_link(self, url=None, err=None, utm_campaign=None):
		specific_url = url is not None
		url = url or "https://mr-beam.org/support"
		params = dict(
			utm_source='beamos',
			utm_medium='beamos',
			utm_campaign=utm_campaign or "hw_malfunction",
			version=self._plugin.get_plugin_version(),
			env=self._plugin.get_env(),
		)
		if err:
			params['error'] = err if isinstance(err, basestring) else ';'.join(err)
		full_url = "{url}?{params}".format(url=url, params=urllib.urlencode(params))
		if specific_url:
			return "<br /><br />" + gettext('For more information check out this %(opening_tag)sKnowledge Base article%(closing_tag)s' % {
				'opening_tag': '<a href="{}" target="_blank"><strong>'.format(full_url),
				'closing_tag': '</strong></a>',
				'line_break': '<br />'
			})
		else:
			return "<br /><br />" + gettext(
				'Browse our %(opening_tag)sKnowledge Base%(closing_tag)s' % {
					'opening_tag': '<a href="{}" target="_blank"><strong>'.format(full_url),
					'closing_tag': '</strong></a>',
				})

	def _get_error_text(self, msg):
		msg = msg if isinstance(msg, basestring) else '<br />'.join(msg)
		return '<br/><br/><strong>' + gettext("Error:") + '</strong><br/>{}'.format(msg)




