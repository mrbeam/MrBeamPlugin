import pandas as pd


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
		valueDf = pd.DataFrame(self.valueList)
		descDict = {
			'median': valueDf.median()
		}
		try:
			describeSeries = valueDf.describe()
			for index in describeSeries.index:
				descDict[index] = describeSeries.loc[index][0]
		except ValueError:
			descDict['error'] = 'ValueError'

		return descDict
