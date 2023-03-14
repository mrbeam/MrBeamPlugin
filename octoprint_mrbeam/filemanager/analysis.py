#!/usr/bin/env python
from octoprint.settings import settings
import octoprint.filemanager.analysis as octo_analysis


class GcodeAnalysisQueue(octo_analysis.GcodeAnalysisQueue):
    """A queue to analyze GCODE files. Analysis results are :class:`dict`
    instances structured as follows:

    @see octoprint.filemanager.analysis.GcodeAnalysisQueue

    .. list-table::
       :widths: 25 70

       - * **Key**
         * **Description**
       - * Nothing
         * Nothing is returned yet to save on cpu.
    """

    def _do_analysis(self, high_priority=False):
        """Perform analysis of a given gocode file Performs the actual analysis
        of the current entry which can be accessed via ``self._current``. Needs
        to be overridden by sub classes.

        Arguments:
            high_priority (bool): Whether the current entry has high priority or not.

        Returns:
            object: The result of the analysis which will be forwarded to the ``finished_callback`` provided during
                construction.
        """
        try:
            # throttle = settings().getFloat(["gcodeAnalysis", "throttle_highprio"]) if high_priority \
            #     else settings().getFloat(["gcodeAnalysis", "throttle_normalprio"])
            # throttle_lines = settings().getInt(["gcodeAnalysis", "throttle_lines"])
            # max_extruders = settings().getInt(["gcodeAnalysis", "maxExtruders"])
            # g90_extruder = settings().getBoolean(["feature", "g90InfluencesExtruder"])
            # speedx = self._current.printer_profile["axes"]["x"]["speed"]
            # speedy = self._current.printer_profile["axes"]["y"]["speed"]
            # offsets = self._current.printer_profile["extruder"]["offsets"]
            # TODO Job time estimation (with pausing when print started?)
            # result = {}
            self._logger.debug("Ignoring analysis of %s" % self._current.absolute_path)
            result = {}
            return result
        finally:
            self._gcode = None


def beam_analysis_queue_factory(callback=None, *args, **kwargs):
    import logging

    return dict(
        gcode=GcodeAnalysisQueue(finished_callback=callback),
    )
