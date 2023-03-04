class WEB:
	def generate_index(self, bme, pms1, pms2, aqi, wlan):
		fp = open("web_index_part1.html", "r")
		yield fp.read()
		fp.close()

		yield "<td>{temp:.1f} F</td>\n<td>{hum:.1f} %</td>\n<td>{press:.1f} mBar</td>\n".format(temp=(bme.temperature * 1.8)+32, hum=bme.humidity, press=bme.pressure)

		fp = open("web_index_part2.html", "r")
		yield fp.read()
		fp.close()

		yield """					<tr class="table-success">
					<!-- <tr class="table-warning"> -->
					<!-- <tr class="table-danger"> -->
"""

		yield "<td>{:d}</td>\n<td>{:d} % ({:d})</td>\n<td>{:d}</td>\n<td>{:d} % ({:d})</td>\n".format(int(aqi.get_aqi_pm2_5()), int(aqi.calc_confidence_pm2_5()), int(abs(pms1.ATM_PM2_5 - pms2.ATM_PM2_5)), int(aqi.get_aqi_pm10_0()), int(aqi.calc_confidence_pm10_0()), int(abs(pms1.ATM_PM10_0 - pms2.ATM_PM10_0)))

		fp = open("web_index_part3.html", "r")
		yield fp.read()
		fp.close()

		yield "<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n".format(pms1.ATM_PM1_0, pms1.ATM_PM2_5, pms1.ATM_PM10_0, pms1.CF1_PM1_0, pms1.CF1_PM2_5, pms1.CF1_PM10_0)

		fp = open("web_index_part4.html", "r")
		yield fp.read()
		fp.close()

		yield "<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n".format(pms2.ATM_PM1_0, pms2.ATM_PM2_5, pms2.ATM_PM10_0, pms2.CF1_PM1_0, pms2.CF1_PM2_5, pms2.CF1_PM10_0)

		fp = open("web_index_part5.html", "r")
		yield fp.read()
		fp.close()

		yield "<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n".format(pms1.RAW_0_3, pms1.RAW_0_5, pms1.RAW_1_0, pms1.RAW_2_5, pms1.RAW_5_0, pms1.RAW_10_0)

		fp = open("web_index_part6.html", "r")
		yield fp.read()
		fp.close()

		yield "<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n<td>{:d}</td>\n".format(pms2.RAW_0_3, pms2.RAW_0_5, pms2.RAW_1_0, pms2.RAW_2_5, pms2.RAW_5_0, pms2.RAW_10_0)

		fp = open("web_index_part7.html", "r")
		yield fp.read()
		fp.close()

		if wlan.isconnected():
			fp = open("web_index_part8.html", "r")
			yield fp.read()
			fp.close()

			yield "<td>{:s}</td>\n<td>{:s}</td>\n<td>{:d}</td>\n".format(wlan.config('essid'), wlan.ifconfig()[0], wlan.status('rssi'))
	
			fp = open("web_index_part9.html", "r")
			yield fp.read()
			fp.close()

		fp = open("web_index_part10.html", "r")
		yield fp.read()
		fp.close()

	def generate_setup(self, scan_data=False, alert_success=False, alert_reboot=False, alert_pass=False):
		fp = open("web_setup_part1.html", "r")
		yield fp.read()
		fp.close()

		if alert_reboot:
			yield "<meta http-equiv=\"refresh\" content=\"30\">\n"
		
		fp = open("web_setup_part2.html", "r")
		yield fp.read()
		fp.close()

		if alert_reboot:
			fp = open("web_setup_reboot.html", "r")
			yield fp.read()
			fp.close()

		if alert_success:
			fp = open("web_setup_success.html", "r")
			yield fp.read()
			fp.close()

		if alert_pass:
			fp = open("web_setup_password.html", "r")
			yield fp.read()
			fp.close()

		fp = open("web_setup_part3.html", "r")
		yield fp.read()
		fp.close()

		if not scan_data == False:
			fp = open("web_setup_part4.html", "r")
			yield fp.read()
			fp.close()

		if not scan_data == False:
			row_count = 0
			row_class = "primary"
			for net in scan_data:
				if (row_count % 2) == 0:
					row_class = "primary"
				else:
					row_class = "secondary"
				row_count = row_count + 1
				security = "No"
				if net[4] > 0:
					security = "Yes"
				yield "<tr class=\"table-{:s}\"><td>{:s}</td><td>{:d}</td><td>{:s}</td></tr>\n".format(row_class, net[0], net[3], security)

		if not scan_data == False:
			yield "</tbody></table>\n"

		fp = open("web_setup_part5.html", "r")
		yield fp.read()
		fp.close()