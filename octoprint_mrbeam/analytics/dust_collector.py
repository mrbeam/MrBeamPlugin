import pandas as pd

class DustCollector(object):

	def __init__(self):
		self.dustValues = list()

	def addDustValue(self,value):
		self.dustValues.append(value)

	def getDustSummary(self):
		"""
		Returns a dict with all the dust statistics
		(mean,median,count,std,)
		:param valueList:
		:return:
		"""
		valueDf = pd.DataFrame(self.dustValues)
		descDict = {
			'median': valueDf.median()
		}
		describeSeries = valueDf.describe()
		for index in describeSeries.index:
			descDict[index] = describeSeries.loc[index][0]
		return descDict

