# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import os
import gc
import machine
import network
import ujson
import led
import utime
from update import Update
import uhashlib
import ubinascii

sw_version = 4
unit_id = ubinascii.hexlify(uhashlib.sha1(machine.unique_id()).digest()).decode('ascii')
setup_pw = (hex(machine.unique_id()[len(machine.unique_id())-3])[2:] + hex(machine.unique_id()[len(machine.unique_id())-2])[2:] + hex(machine.unique_id()[len(machine.unique_id())-1])[2:]).upper()

# Set up a global for our wlan objects
wlan = network.WLAN(network.STA_IF)
wlan.active(False)

wlan_ap = network.WLAN(network.AP_IF)
wlan_ap.ifconfig(('192.168.42.1', '255.255.255.0', '192.168.42.1', '1.1.1.1'))
wlan_ap.config(essid='NVH_AQI', password=("NVHAQI" + setup_pw), authmode=3)
wlan_ap.active(False)

# Configure our LED instance
rgbled = led.led()

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("NVH AQI SENSOR - SW VERS: {:d} - ID: {:s} - PW: {:s}".format(sw_version, unit_id, setup_pw))
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

# Define some default preferences in case there isn't a saved preferences file
prefs_file_path = 'prefs.json'
prefs_set = False
prefs = {	'WIFI': {
				'NETWORK': 'NVH_AQI',
				'PASSWORD': ("NVHAQI" + setup_pw)
			},
			'SERVERS': {
				'NTP_SERVER': "time.nullroutenetworks.com",
				'POST_URL': "https://127.0.0.1/submit.php",
				'UPDATE_URL': "https://127.0.0.1/hw_v1_0/"
			}
		}

# Check if we have a saved preferences file
print("Load prefs...")
if prefs_file_path in os.listdir():
	# Prefs file exists, read it in
	with open(prefs_file_path) as prefs_fp:
		prefs_file = ujson.load(prefs_fp)
		
		prefs_changes = False
		
		if 'WIFI' not in prefs_file.keys():
			prefs_file['WIFI'] = prefs['WIFI']
			prefs_changes = True
		if 'NETWORK' not in prefs_file['WIFI'].keys():
			prefs_file['WIFI']['NETWORK'] = prefs['WIFI']['NETWORK']
			prefs_changes = True
		if 'PASSWORD' not in prefs_file['WIFI'].keys():
			prefs_file['WIFI']['PASSWORD'] = prefs['WIFI']['PASSWORD']
			prefs_changes = True
		if 'SERVERS' not in prefs_file.keys():
			prefs_file['SERVERS'] = prefs['SERVERS']
			prefs_changes = True
		if 'NTP_SERVER' not in prefs_file['SERVERS'].keys():
			prefs_file['SERVERS']['NTP_SERVER'] = prefs['SERVERS']['NTP_SERVER']
			prefs_changes = True
		if 'POST_URL' not in prefs_file['SERVERS'].keys():
			prefs_file['SERVERS']['POST_URL'] = prefs['SERVERS']['POST_URL']
			prefs_changes = True
		if 'UPDATE_URL' not in prefs_file['SERVERS'].keys():
			prefs_file['SERVERS']['UPDATE_URL'] = prefs['SERVERS']['UPDATE_URL']
			prefs_changes = True

		if prefs_changes:
			print("Prefs file requires updates. Saving.")
			settings_json = ujson.dumps(prefs_file)
			try:
				prefs_filep = open(prefs_file_path, 'w')
				prefs_filep.write(settings_json)
				prefs_filep.close()
			except Exception as e:
				print("EXCEPTION: %s" % e)

		prefs = prefs_file

	prefs_set = True
	print("Prefs loaded.")
else:
	print("No prefs. Using defaults.")

# Check for updates
if prefs_set:
	rgbled.blink = False
	rgbled.color = rgbled.PURPLE
	rgbled.step()
	
	print("Connect WiFi...")
	wlan.active(True)
	wlan.connect(prefs['WIFI']['NETWORK'], prefs['WIFI']['PASSWORD'])
	wifi_connect_wait = 0
	while not wlan.isconnected():
		utime.sleep(1)
		wifi_connect_wait = wifi_connect_wait + 1
		if wifi_connect_wait > 10:
			print("No WiFi.")
			wlan.disconnect()
			break

	if wlan.isconnected():
		print("Check for update...")
		try:
			OTA = Update(url=prefs['SERVERS']['UPDATE_URL'], sw_vers=sw_version)
			if OTA.check_update():
				print("Update available. Download...")
				print("Free Mem: %d" % gc.mem_free())
				if OTA.install_update():
					machine.reset()
			else:
				print("No update. Continue startup.")
		except Exception as e:
			print("Exception OTA: ")
			print(e)

		del OTA
		
	wlan.disconnect()
	wlan.active(False)
	
del Update, uhashlib, ubinascii
gc.collect()
