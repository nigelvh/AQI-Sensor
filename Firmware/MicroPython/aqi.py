class AQI:
	AVG_ARRAY_LEN = const(60)

	def __init__(self, pms1=None, pms2=None, bme=None):
		# Validate inputs
		if pms1 is None:
			raise ValueError("Invalid pms object.")
		if pms2 is None:
			raise ValueError("Invalid pms object.")
		if bme is None:
			raise ValueError("Invalid bme object.")

		self._pms1 = pms1
		self._pms2 = pms2
		self._bme = bme
	
	def get_aqi_pm2_5(self, corrected=False):
		if corrected:
			return self._calc_aqi_pm2_5(self._get_epa_corrected_pm2_5())
		else:
			return self._calc_aqi_pm2_5(self._get_sensors_avg_pm2_5())
	
	def _get_epa_corrected_pm2_5(self):
		return (0.534 * self._get_sensors_avg_pm2_5()) - (0.0844 * self._bme.humidity) + 5.604
	
	def get_aqi_pm10_0(self):
		return self._calc_aqi_pm10_0(self._get_sensors_avg_pm10_0())
	
	def _calc_aqi_pm2_5(self, value):
		if value > 350.5:
			return self._scale_aqi(value, 500, 401, 500, 350.5)
		elif value > 250.5:
			return self._scale_aqi(value, 400, 301, 350.4, 250.5)
		elif value > 150.5:
			return self._scale_aqi(value, 300, 201, 250.4, 150.5)
		elif value > 55.5:
			return self._scale_aqi(value, 200, 151, 150.4, 55.5)
		elif value > 35.5:
			return self._scale_aqi(value, 150, 101, 55.4, 35.5)
		elif value > 12.1:
			return self._scale_aqi(value, 100, 51, 35.4, 12.1)
		elif value >= 0:
			return self._scale_aqi(value, 50, 0, 12, 0)
		else:
			return False
	
	def _calc_aqi_pm10_0(self, value):
		if value > 505:
			return self._scale_aqi(value, 500, 401, 604, 505)
		elif value > 425:
			return self._scale_aqi(value, 400, 301, 504, 425)
		elif value > 355:
			return self._scale_aqi(value, 300, 201, 424, 355)
		elif value > 255:
			return self._scale_aqi(value, 200, 151, 354, 255)
		elif value > 155:
			return self._scale_aqi(value, 150, 101, 254, 155)
		elif value > 55:
			return self._scale_aqi(value, 100, 51, 154, 55)
		elif value >= 0:
			return self._scale_aqi(value, 50, 0, 54, 0)
		else:
			return False
	
	def _scale_aqi(self, value, index_high, index_low, value_high, value_low):
		return int((((index_high - index_low) / (value_high - value_low)) * (value - value_low)) + index_low)
	
	def _get_sensors_avg_pm2_5(self):
		if (self._pms1.LAST_UPDATE < 60000) and (self._pms2.LAST_UPDATE < 60000):
			return (self._pms1.get_average_2_5() + self._pms2.get_average_2_5()) / 2
		elif (self._pms1.LAST_UPDATE < 60000):
			return self._pms1.get_average_2_5()
		elif (self._pms2.LAST_UPDATE < 60000):
			return self._pms2.get_average_2_5()
		else:
			return 0

	def _get_sensors_avg_pm10_0(self):
		if (self._pms1.LAST_UPDATE < 60000) and (self._pms2.LAST_UPDATE < 60000):
			return (self._pms1.get_average_10_0() + self._pms2.get_average_10_0()) / 2
		elif (self._pms1.LAST_UPDATE < 60000):
			return self._pms1.get_average_10_0()
		elif (self._pms2.LAST_UPDATE < 60000):
			return self._pms2.get_average_10_0()
		else:
			return 0

	def calc_confidence_pm2_5(self):
		sensorDiffRaw = abs(self._pms1.get_average_2_5() - self._pms2.get_average_2_5())
		if sensorDiffRaw < 5:
			return 100
		sensorDiffPct = 100 - ((sensorDiffRaw / self._get_sensors_avg_pm2_5()) * 100)
		return sensorDiffPct

	def calc_confidence_pm10_0(self):
		sensorDiffRaw = abs(self._pms1.get_average_10_0() - self._pms2.get_average_10_0())
		if sensorDiffRaw < 5:
			return 100
		sensorDiffPct = 100 - ((sensorDiffRaw / self._get_sensors_avg_pm10_0()) * 100)
		return sensorDiffPct