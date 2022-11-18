import numpy as np
from octoprint_mrbeam.mrb_logger import mrb_logger


class ValueCollector(object):
    def __init__(self, name):
        self.name = name
        self.valueList = list()
        # self._logger = mrb_logger("octoprint.plugins.mrbeam.analyticshandler")

    def addValue(self, value):
        self.valueList.append(value)

    def getSummary(self):
        """Returns a dict with all the dust statistics (mean,median,count,std,)

        :param valueList:
        :return:
        """
        count = len(self.valueList)
        # self._logger.debug('Collector <{}> has values: {}'.format(self.name,self.valueList))

        if count > 0:
            arr = np.asarray(self.valueList)
            descDict = {
                "median": np.median(arr),
                "mean": np.mean(arr),
                "min": min(self.valueList),
                "max": max(self.valueList),
                "25p": np.percentile(arr, 25),
                "75p": np.percentile(arr, 75),
                "std": np.std(arr),
                "count": len(self.valueList),
            }
        else:
            descDict = {"count": count}

        # make all values float for json.dump()-compability
        for key in descDict:
            descDict[key] = round(descDict[key], 4)

        return descDict

    def get_latest_value(self):
        """
        Returns the most recent element of the ValueCollector
        :return:
        """
        try:
            return round(self.valueList[-1], 4)
        except:  # mainly for IndexError
            return None
