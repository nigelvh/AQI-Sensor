import os
import gc
import ujson
import urequests
import uhashlib
import ubinascii

class Update:
	def __init__(self, url=None, sw_vers=None):
		if url is None:
			raise ValueError("Invalid updates url.")
		if sw_vers is None:
			raise Valueerror("Invalid software version.")
			
		self._base_url = url
		self._current_sw_vers = sw_vers

	def check_update(self):
		response = urequests.get(self._base_url + "/version.json")
		if response.status_code == 200:
			data = ujson.loads(response.text)
			response.close()
			if 'VERSION' in data.keys():
				new_sw_version = int(data['VERSION'])
				if new_sw_version > self._current_sw_vers:
					return True
				else:
					return False
			else:
				print("Error getting update version number.")
				return False
		else:
			response.close()
			print("Error getting update version.json")
			return False

	def install_update(self):
		response = urequests.get(self._base_url + "/version.json")
		if response.status_code == 200:
			data = ujson.loads(response.text)
			response.close()
			if 'VERSION' in data.keys():
				new_sw_version = int(data['VERSION'])
				if new_sw_version > self._current_sw_vers:
					# Loop through all the files in the list, download them and verify checksums, store them to temp files
					for file in data['FILES']:
						print("Downloading file - NAME: {:s}, SHASUM: {:s}".format(data['FILES'][file]['NAME'], data['FILES'][file]['SHASUM']))
						
						file_dl = urequests.get(self._base_url + "/" + data['FILES'][file]['NAME'])
						if file_dl.status_code != 200:
							print("Unable to grab file. Stopping update.")
							file_dl.close()
							return False
						
						file_sha_obj = uhashlib.sha1(file_dl.content)
						file_dl_sha = ubinascii.hexlify(file_sha_obj.digest()).decode('ascii')
						if not (file_dl_sha == data['FILES'][file]['SHASUM']):
							print("Checksum of downloaded file did not match. Stopping update.")
							file_dl.close()
							return False
						
						with open('new_' + data['FILES'][file]['NAME'], 'wb') as fp:
							fp.write(file_dl.content)
							fp.close()
						
						del file_sha_obj, file_dl_sha
						file_dl.close()
						gc.collect()
					
					# If we've gotten here, we've completed looping through all the files without failing out. Swap the new files in for the old ones.
					print("All files downloaded successfully. Upgrading code...")
					for file in data['FILES']:
						print("Replacing {:s}.".format(data['FILES'][file]['NAME']))
						try:
							os.remove(data['FILES'][file]['NAME'])
						except Exception as e:
							print("Old version didn't exist. Continuing.")
						os.rename('new_' + data['FILES'][file]['NAME'], data['FILES'][file]['NAME'])
					
					print("Upgrade complete. Reboot to take effect.")
					return True
						
				else:
					return False
			else:
				print("Error getting update version number.")
				return False
		else:
			print("Error getting update version.json")
			return False		