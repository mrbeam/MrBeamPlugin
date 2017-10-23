import numpy as np

class ValueCollector(object):
	def __init__(self):
		self.valueList = list()

	def addValue(self, value):
		self.valueList.append(value)

	def getSummary(self):
		"""
		Returns a dict with all the dust statistics
		(mean,median,count,std,)
		:param valueList:
		:return:
		"""
		arr = np.ndarray(self.valueList)

		descDict = {
				'median': np.median(arr),
				'mean': np.mean(arr),
				'min': min(self.valueList),
				'max': max(self.valueList),
				'25p': np.percentile(arr,25),
				'75p': np.percentile(arr,75),
				'std': np.std(arr),
				'count': len(self.valueList)
		}

		# make all values float for json.dump()-compability
		for key in descDict:
			descDict[key] = round(descDict[key],4)

		return descDict

	def get_latest_value(self):
		"""
		Returns the most recent element of the ValueCollector
		:return:
		"""
		return round(self.valueList[-1],4)
