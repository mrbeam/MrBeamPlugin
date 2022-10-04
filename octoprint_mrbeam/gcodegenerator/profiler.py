import time
import logging


class Profiler:
    def __init__(self, sessionName):
        self.name = sessionName
        self.eventlog = []
        self.events = {}
        self.sessionDuration = -1
        self.sessionStart = time.time()
        self.lastStopped = self.sessionStart
        try:
            from octoprint_mrbeam.mrb_logger import init_mrb_logger, mrb_logger

            self.log = mrb_logger("octoprint.plugins.gcodegenerator.profiler")
        except ImportError:
            # when called via command line
            self.log = logging.getLogger("octoprint.plugins.gcodegenerator.profiler")

    def start(self, eventname):
        ts = time.time()
        self.eventlog.append((0, eventname, "start", ts))
        self.events[eventname] = ts
        return self

    def stop(self, eventname):
        ts = time.time()
        start = self.lastStopped
        if eventname in self.events:
            start = self.events[eventname]
            del self.events[eventname]
        duration = ts - start
        self.eventlog.append((duration, eventname, "stop", ts))
        return self

    def nest_data(self, otherProfiler):
        otherProfiler.finalize()
        otherName = otherProfiler.name
        for event in otherProfiler.eventlog:
            tmp = (event[0], " %s_%s" % (otherName, event[1]), event[2], event[3])
            self.log.info(tmp)
            self.eventlog.append(tmp)

        return self

    def stopAll(self):
        for n in self.events.keys():
            self.stop(n)

        return self

    def finalize(self):
        self.stopAll()
        self.sessionDuration = time.time() - self.sessionStart
        return self

    def getSummary(self):
        self.stopAll()
        summary = ["%f %s %s: %.4fs" % x for x in self.eventlog]
        return (
            "Profiling session %s (total: %.4f):\n" % (self.name, self.sessionDuration)
        ) + "\n".join(summary)

    def getShortSummary(self):
        self.stopAll()

        summary = []
        for x in self.eventlog:
            if x[2] == "stop":
                val = 100 * x[0] / self.sessionDuration
                summary.append(f"{val:6.2f}% {x[1]}")

        return (
            ("Profiling session %s:\n" % self.name)
            + "\n".join(summary)
            + "\nTotal: %.4fs" % self.sessionDuration
        )
