import urequests
import ntptime
import uasyncio
import re
import sensor
import aqi
import web
from microdot_asyncio import Microdot, Response, send_file

# Set up our microdot app instance
app = Microdot()
Response.default_content_type = 'text/html'
web = web.WEB()

ntptime.host = prefs['SERVERS']['NTP_SERVER']

# Configure our BME instance
i2c = machine.I2C(1, scl=machine.Pin(22), sda=machine.Pin(21), freq=100000)
bme = sensor.BME280(i2c=i2c)
bme.start(standby=bme.BME_STANDBY_MS_62_5, filter=bme.BME_FILTER_4)

# Configure our PMS7003 instances
uart1 = machine.UART(1, baudrate=9600, bits=8, parity=None, stop=1, tx=13, rx=14, timeout=2000, timeout_char=2000)
uart2 = machine.UART(2, baudrate=9600, bits=8, parity=None, stop=1, tx=17, rx=16, timeout=2000, timeout_char=2000)
pms1 = sensor.PMS7003(uart=uart1)
pms2 = sensor.PMS7003(uart=uart2)

# Configure our AQI objects
aqi = aqi.AQI(pms1, pms2, bme)

# Define a flag for if a reboot has been requested
reboot_flag = False
reboot_time = 0

# Run 'mode' flag
run_mode = 0

# Validate that the string contains only printable ASCII chars
def wifi_match(strg):
	return bool(re.search(r'[ -~]$', strg))

@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
async def web_index(request):
	return web.generate_index(bme, pms1, pms2, aqi, wlan)

@app.route('/setup', methods=['GET', 'POST'])
@app.route('/setup.html', methods=['GET', 'POST'])
async def web_setup(request):
	alert_success_flag = False
	alert_reboot_flag = False
	alert_pass_flag = False
	global reboot_flag
	global reboot_time
	
	wlan_scan = wlan.scan()
	
	if request.method == 'POST':
		print(request.form)
		if request.form.get('submit') is not None:
			if request.form.get('passwd').lower() == setup_pw.lower():
				print('Setup page got submit request. Saving data...')
				print('SSID: %s\nPASS: %s\n' % (request.form.get('ssid'), request.form.get('pass')))
				if wifi_match(request.form.get('ssid')) and (wifi_match(request.form.get('pass')) or (len(request.form.get('pass')) == 0)):
					prefs['WIFI']['NETWORK'] = request.form.get('ssid')
					prefs['WIFI']['PASSWORD'] = request.form.get('pass')
					settings_json = ujson.dumps(prefs)
					try:
						prefs_fp = open(prefs_file_path, 'w')
						prefs_fp.write(settings_json)
						prefs_fp.close()
						alert_success_flag = True
					except Exception as e:
						print("EXCEPTION: %s" % e)
				else:
					print('Failed to validate wifi SSID and PASS.')
			else:
				print('Incorrect setup password')
				alert_pass_flag = True
		if request.form.get('reboot') is not None:
			if request.form.get('passwd').lower() == setup_pw.lower():
				print('Setup page got reboot request. Rebooting...')
				reboot_flag = True
				reboot_time = utime.ticks_ms()
				alert_reboot_flag = True
			else:
				print('Incorrect setup password')
				alert_pass_flag = True
		if request.form.get('defaults') is not None:
			if request.form.get('passwd').lower() == setup_pw.lower():
				print('Setup page got defaults reset request. Clearing prefs and rebooting...')
				try:
					os.remove(prefs_file_path)
				except Exception as e:
					print("EXCEPTION: %s" % e)
				reboot_flag = True
				reboot_time = utime.ticks_ms()
				alert_reboot_flag = True
			else:
				print('Incorrect setup password')
				alert_pass_flag = True
				
	return web.generate_setup(scan_data=wlan_scan, alert_success=alert_success_flag, alert_reboot=alert_reboot_flag, alert_pass=alert_pass_flag)

@app.route('/style.css')
async def web_bootstrap_css(request):
	return send_file('style.css')

# Background task on 1 minute timer
async def loop_1m():
	upload_fail_count = 0
	
	while(True):
		await uasyncio.sleep(60)

		# Read sensors
		bme.read()
		pms1.fresh_read()
		pms2.fresh_read()

		# At 15 minutes past the hour, update time via NTP
		if utime.localtime()[4] == 15:
			print("Sync time: {:s}".format(prefs['SERVERS']['NTP_SERVER']))
			try:
				ntptime.settime()
				print("Updated time：%s" %str(utime.localtime()))
			except:
				print("ERR: NTP")

		# Output some data
		pre_gc_free = gc.mem_free()
		gc.collect()
		post_gc_free = gc.mem_free()

		print("MEM - PRE: %d, POST: %d" % (pre_gc_free, post_gc_free))
		print("AQI - PM2.5: %d, PM10.0: %d" % (aqi.get_aqi_pm2_5() , aqi.get_aqi_pm10_0()))
		print("PMS1 AGE: %d, PMS2 AGE: %d" % ((utime.ticks_ms() - pms1.LAST_UPDATE), (utime.ticks_ms() - pms2.LAST_UPDATE)))
		print("ENV - TEMP: %f, HUM: %f, PRESS: %f" % (bme.temperature, bme.humidity, bme.pressure))

		if wlan.isconnected():
			post_headers = {'content-type': 'application/json'}
			post_data = {'NODE': {
							'MAC': hex(wlan.config('mac')[0])[2:] + ":" + hex(wlan.config('mac')[1])[2:] + ":" + hex(wlan.config('mac')[2])[2:] + ":" + hex(wlan.config('mac')[3])[2:] + ":" + hex(wlan.config('mac')[4])[2:] + ":" + hex(wlan.config('mac')[5])[2:],
							'SW_VERS_NUM': sw_version,
							'UNIT_ID': unit_id,
							'TIMESTAMP': utime.localtime(),
							'RESET_CAUSE': machine.reset_cause(),
							'RESET_TIME': utime.ticks_ms(),
							'FAIL_COUNT': upload_fail_count
							},
						'CONNECTION': {
							'NETWORK': wlan.config('essid'),
							'RSSI': wlan.status('rssi'),
							'IP': wlan.ifconfig()[0]
							},
						'DATA': {
							'ENVIRONMENT': {
								'TEMPERATURE': bme.temperature,
								'PRESSURE': bme.pressure,
								'HUMIDITY': bme.humidity
								},
							'AQI': {
								'AQI_PM2_5': int(aqi.get_aqi_pm2_5()),
								'AQI_PM2_5_CONFIDENCE': int(aqi.calc_confidence_pm2_5()),
								'AQI_PM10_0': int(aqi.get_aqi_pm10_0()),
								'AQI_PM10_0_CONFIDENCE': int(aqi.calc_confidence_pm10_0())
								},
							'PARTICULATE': {
								'SENSOR_A': {
									'1HR_AVG_PM2_5': pms1.get_average_2_5(),
									'1HR_AVG_PM10_0': pms1.get_average_10_0(),
									'CF1_PM1_0': pms1.CF1_PM1_0,
									'CF1_PM2_5': pms1.CF1_PM2_5,
									'CF1_PM10_0': pms1.CF1_PM10_0,
									'ATM_PM1_0': pms1.ATM_PM1_0,
									'ATM_PM2_5': pms1.ATM_PM2_5,
									'ATM_PM10_0': pms1.ATM_PM10_0,
									'RAW_0_3': pms1.RAW_0_3,
									'RAW_0_5': pms1.RAW_0_5,
									'RAW_1_0': pms1.RAW_1_0,
									'RAW_2_5': pms1.RAW_2_5,
									'RAW_5_0': pms1.RAW_5_0,
									'RAW_10_0': pms1.RAW_10_0,
									'VERSION': pms1.VERSION,
									'ERROR': pms1.ERROR,
									'LAST_UPDATE': (utime.ticks_ms() - pms1.LAST_UPDATE)
									},
								'SENSOR_B': {
									'1HR_AVG_PM2_5': pms2.get_average_2_5(),
									'1HR_AVG_PM10_0': pms2.get_average_10_0(),
									'CF1_PM1_0': pms2.CF1_PM1_0,
									'CF1_PM2_5': pms2.CF1_PM2_5,
									'CF1_PM10_0': pms2.CF1_PM10_0,
									'ATM_PM1_0': pms2.ATM_PM1_0,
									'ATM_PM2_5': pms2.ATM_PM2_5,
									'ATM_PM10_0': pms2.ATM_PM10_0,
									'RAW_0_3': pms2.RAW_0_3,
									'RAW_0_5': pms2.RAW_0_5,
									'RAW_1_0': pms2.RAW_1_0,
									'RAW_2_5': pms2.RAW_2_5,
									'RAW_5_0': pms2.RAW_5_0,
									'RAW_10_0': pms2.RAW_10_0,
									'VERSION': pms2.VERSION,
									'ERROR': pms2.ERROR,
									'LAST_UPDATE': (utime.ticks_ms() - pms2.LAST_UPDATE)
									}
								}
							}
						}

			gc.collect()

			try:
				result = urequests.post(prefs['SERVERS']['POST_URL'], headers = post_headers, data = ujson.dumps(post_data))
				result.close()
			except Exception as e:
				print("ERR: Upload sensor data")
				print(e)
				upload_fail_count = upload_fail_count + 1
			else:
				print("Data uploaded.")
				upload_fail_count = 0
		else:
			print("ERR: No WiFi during upload!")
		
		if upload_fail_count > 15:
			print("ERR: Upload fail count")
			machine.reset()

# Background task on 1 second timer
async def loop_1s():
	while(True):
		# Check for reboot flag
		if reboot_flag:
			print("Reboot flag. Diff: %d" % utime.ticks_diff(utime.ticks_ms(), reboot_time))
			if utime.ticks_diff(utime.ticks_ms(), reboot_time) > 5000:
				machine.reset()
		
		# Run some garbage collection
		if gc.mem_free() < 32768:
			print("GC TASK: Free Mem: %d" % gc.mem_free(), end=" ")
			gc.collect()
			print("GC TASK: Collect... Free Mem: %d" % gc.mem_free())
				
		await uasyncio.sleep_ms(1000)

async def main():
	global run_mode
	while(True):
		# If we don't have a preferences file, enter setup mode
		if prefs_set == False:
			rgbled.blink = True
			rgbled.color = rgbled.ORANGE
		
			wlan.active(True)
			wlan_ap.active(True)
			
			print('No configuration. Enter setup. Start AP.')
			print('Network:', wlan_ap.ifconfig())
			print('Reboot in 10 min.')
			
			await uasyncio.sleep(600)
			print('10 min expired. Reboot...')
			machine.reset()
			
		else:
			# Run mode 0 - Fresh boot, try to connect to a hotspot for config
			if run_mode == 0:
				rgbled.blink = True
				rgbled.color = rgbled.TEAL
			
				if not wlan.isconnected():
					print('Trying setup net...')
					wlan_ap.active(False)
					wlan.active(True)
					wlan.connect('NVH_AQI', ("NVHAQI" + setup_pw))
					wifi_connect_wait = 0
					while not wlan.isconnected():
						await uasyncio.sleep(1)
						wifi_connect_wait = wifi_connect_wait + 1
						if wifi_connect_wait > 10:
							print("No setup network. Normal boot...")
							wlan.disconnect()
							run_mode = 1
							break
					
					if wlan.isconnected():
						# We were able to connect to the config network
						print('Setup network! Reboot in 10 min.')
						print('Network:', wlan.ifconfig())
						rgbled.blink = False
						await uasyncio.sleep(600)
						print('10 min expired. Reboot...')
						machine.reset()
			
			# Run mode 1 - Fresh boot, after we've tried finding the config hotspot, connect to normal wifi config
			elif run_mode == 1:
				rgbled.blink = True
				rgbled.color = rgbled.BLUE
			
				print('Connect to wifi...')
				wlan_ap.active(False)
				wlan.active(True)
				wlan.disconnect()
				wlan.connect(prefs['WIFI']['NETWORK'], prefs['WIFI']['PASSWORD'])
				wifi_connect_wait = 0
				while not wlan.isconnected():
					await uasyncio.sleep(1)
					wifi_connect_wait = wifi_connect_wait + 1
					if wifi_connect_wait > 30:
						print("Not connected.")
						wlan.disconnect()
						run_mode = 2
						break
				
				if wlan.isconnected():
					# We were able to connect to the normal wifi config
					rgbled.blink = False
					print('Connect success!')
					print('Network:', wlan.ifconfig())
					run_mode = 3
			
			# Run mode 2 - Failed to connect to normal wifi config
			elif run_mode == 2:
				rgbled.blink = True
				rgbled.color = rgbled.RED

				wlan.active(True)
				wlan_ap.active(True)
			
				print('No WiFi. Enter setup. Start AP.')
				print('Network:', wlan_ap.ifconfig())
				print('Reboot in 10 min.')
			
				await uasyncio.sleep(600)
				print('10 min expired. Reboot...')
				machine.reset()
			
			# Run mode 3 - Connected to normal wifi
			elif run_mode == 3:
				rgbled.blink = False
				rgbled.color = rgbled.GREEN
				
				print("Sync time: {:s}".format(prefs['SERVERS']['NTP_SERVER']))
				try:
					ntptime.settime()
					print("Updated time：%s" %str(utime.localtime()))
				except:
					print("ERR: NTP")

				await uasyncio.sleep(2)
				rgbled.blink = False
				rgbled.color = rgbled.BLACK

				wifi_fail_count = 0
				while(True):
					# Keep track of if we've lost wifi
					if wlan.isconnected():
						wifi_fail_count = 0
					else:
						wifi_fail_count = wifi_fail_count + 1
					
					# If we've lost wifi for more than 15 minutes, reboot.
					if wifi_fail_count > 15:
						machine.reset()
					
					await uasyncio.sleep(60)

		# Do stuff
		await uasyncio.sleep_ms(2000)
			
# MAIN
try:
	# Background tasks
	uasyncio.create_task(loop_1s())
	uasyncio.create_task(loop_1m())
	uasyncio.create_task(rgbled.run())
	uasyncio.create_task(main())
	app.run(host='0.0.0.0', port=80)

except Exception as e:
	# Potentially do something with the exception
	print("EXCEPTION:")
	print(e)
	print("Reset...")
	machine.reset()