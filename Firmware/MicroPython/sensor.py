import math
import utime
import struct

class PMS7003:
	# Start Bytes
	PMS_START_BYTE_1 = const(0x42)
	PMS_START_BYTE_2 = const(0x4D)

	# Data Field Positions
	PMS_FIELD_POS_FRAME_LENGTH = const(0)
	PMS_FIELD_POS_CF1_PM1_0 = const(1)
	PMS_FIELD_POS_CF1_PM2_5 = const(2)
	PMS_FIELD_POS_CF1_PM10_0 = const(3)
	PMS_FIELD_POS_ATM_PM1_0 = const(4)
	PMS_FIELD_POS_ATM_PM2_5 = const(5)
	PMS_FIELD_POS_ATM_PM10_0 = const(6)
	PMS_FIELD_POS_RAW_0_3 = const(7)
	PMS_FIELD_POS_RAW_0_5 = const(8)
	PMS_FIELD_POS_RAW_1_0 = const(9)
	PMS_FIELD_POS_RAW_2_5 = const(10)
	PMS_FIELD_POS_RAW_5_0 = const(11)
	PMS_FIELD_POS_RAW_10_0 = const(12)
	PMS_FIELD_POS_VERSION = const(13)
	PMS_FIELD_POS_ERROR = const(14)
	PMS_FIELD_POS_CHECKSUM = const(15)

	def __init__(self, uart=None, avg_samples=60):
		# Validate inputs
		if uart is None:
			raise ValueError("Invalid uart object.")
		
		self._uart = uart
		self._avg_samples_len = avg_samples
		
		self.LAST_UPDATE = 0
		self.CF1_PM1_0 = 0
		self.CF1_PM2_5 = 0
		self.CF1_PM10_0 = 0
		self.ATM_PM1_0 = 0
		self.ATM_PM2_5 = 0
		self.ATM_PM10_0 = 0
		self.RAW_0_3 = 0
		self.RAW_0_5 = 0
		self.RAW_1_0 = 0
		self.RAW_2_5 = 0
		self.RAW_5_0 = 0
		self.RAW_10_0 = 0
		self.VERSION = 0
		self.ERROR = 0

		self._avg_samples_2_5 = []
		self._avg_samples_10_0 = []
		for x in range(self._avg_samples_len):
			self._avg_samples_2_5.append(0)
			self._avg_samples_10_0.append(0)
		
		self.fresh_read()
		for x in range(self._avg_samples_len):
			self._avg_samples_2_5[x] = self.ATM_PM2_5
			self._avg_samples_10_0[x] = self.ATM_PM10_0

	def fresh_read(self):
		self._flush_input()
		return self.read()
	
	def read(self):
		# Loop through at most 32 bytes looking for the start byte
		loops = 0
		while True:
			temp_start_1 = self._read_byte()
			if temp_start_1 is False:
				return False
			if ord(temp_start_1) == self.PMS_START_BYTE_1:
				break
			loops = loops + 1
			if loops > 32:
				return False

		# After we've found the start byte, look for the second start byte
		temp_start_2 = self._read_byte()
		if temp_start_2 is False:
			return False
		if ord(temp_start_2) != self.PMS_START_BYTE_2:
			return False
	
		# We've gotten both start bytes, grab the next 30 bytes of data
		frame_data = self._read_num_bytes(30)
		if frame_data is False:
			return False
		
		# Unpack the binary data
		data = struct.unpack('!HHHHHHHHHHHHHBBH', frame_data)
		
		# Validate the checksum
		checksum = self.PMS_START_BYTE_1 + self.PMS_START_BYTE_2 + sum(frame_data[:28])
		if checksum != data[self.PMS_FIELD_POS_CHECKSUM]:
			print("Checksum invalid.")
			return False
		
		# Save the data and update the LAST_UPDATE var
		self.CF1_PM1_0 = data[self.PMS_FIELD_POS_CF1_PM1_0]
		self.CF1_PM2_5 = data[self.PMS_FIELD_POS_CF1_PM2_5]
		self.CF1_PM10_0 = data[self.PMS_FIELD_POS_CF1_PM10_0]
		self.ATM_PM1_0 = data[self.PMS_FIELD_POS_ATM_PM1_0]
		self.ATM_PM2_5 = data[self.PMS_FIELD_POS_ATM_PM2_5]
		self.ATM_PM10_0 = data[self.PMS_FIELD_POS_ATM_PM10_0]		
		self.RAW_0_3 = data[self.PMS_FIELD_POS_RAW_0_3]
		self.RAW_0_5 = data[self.PMS_FIELD_POS_RAW_0_5]
		self.RAW_1_0 = data[self.PMS_FIELD_POS_RAW_1_0]
		self.RAW_2_5 = data[self.PMS_FIELD_POS_RAW_2_5]
		self.RAW_5_0 = data[self.PMS_FIELD_POS_RAW_5_0]
		self.RAW_10_0 = data[self.PMS_FIELD_POS_RAW_10_0]
		self.VERSION = data[self.PMS_FIELD_POS_VERSION]
		self.ERROR = data[self.PMS_FIELD_POS_ERROR]
		self.LAST_UPDATE = utime.ticks_ms()

		self._avg_samples_2_5.insert(0, self.ATM_PM2_5)
		self._avg_samples_2_5.pop()
		self._avg_samples_10_0.insert(0, self.ATM_PM10_0)
		self._avg_samples_10_0.pop()

		return True

	def get_average_2_5(self):
		return sum(self._avg_samples_2_5) / len(self._avg_samples_2_5)

	def get_average_10_0(self):
		return sum(self._avg_samples_10_0) / len(self._avg_samples_10_0)
	
	def _debug_avg_2_5(self):
		for x in range(len(self._avg_samples_2_5)):
			print(self._avg_samples_2_5[x])

	def _debug_avg_10_0(self):
		for x in range(len(self._avg_samples_10_0)):
			print(self._avg_samples_10_0[x])

	def _flush_input(self):
		loops = 0
		while(self._uart.any() > 0):
			self._uart.read(self._uart.any())
			loops = loops + 1
			if loops > 255:
				break
		return True
	
	def _read_byte(self):
		working = self._uart.read(1)
		if (working is None) or (len(working) < 1):
			return False
		return working
	
	def _read_num_bytes(self, num_bytes):
		working = self._uart.read(num_bytes)
		if (working is None) or (len(working) < num_bytes):
			return False
		return working

class BME280:
	# Oversampling Options
	BME_OVERSAMPLE_SKIP = const(0)
	BME_OVERSAMPLE_X1 = const(1)
	BME_OVERSAMPLE_X2 = const(2)
	BME_OVERSAMPLE_X4 = const(3)
	BME_OVERSAMPLE_X8 = const(4)
	BME_OVERSAMPLE_X16 = const(5)

	# Filter Coefficient Options
	BME_FILTER_OFF = const(0)
	BME_FILTER_2 = const(1)
	BME_FILTER_4 = const(2)
	BME_FILTER_8 = const(3)
	BME_FILTER_16 = const(4)

	# Normal Mode Standby Time Options
	BME_STANDBY_MS_0_5 = const(0)
	BME_STANDBY_MS_62_5 = const(1)
	BME_STANDBY_MS_125 = const(2)
	BME_STANDBY_MS_250 = const(3)
	BME_STANDBY_MS_500 = const(4)
	BME_STANDBY_MS_1000 = const(5)
	BME_STANDBY_MS_10 = const(6)
	BME_STANDBY_MS_20 = const(7)

	# Sampling Mode
	BME_MODE_SLEEP = const(0)
	BME_MODE_FORCED = const(1)
	BME_MODE_NORMAL = const(3)

	# Chip Data
	BME_REGISTER_CHIPID = const(0xD0)
	BME_REGISTER_VERSION = const(0xD1)

	# Calibration Data
	BME_REGISTER_COMP_T1 = const(0x88)
	BME_REGISTER_COMP_T2 = const(0x8A)
	BME_REGISTER_COMP_T3 = const(0x8C)
	BME_REGISTER_COMP_P1 = const(0x8E)
	BME_REGISTER_COMP_P2 = const(0x90)
	BME_REGISTER_COMP_P3 = const(0x92)
	BME_REGISTER_COMP_P4 = const(0x94)
	BME_REGISTER_COMP_P5 = const(0x96)
	BME_REGISTER_COMP_P6 = const(0x98)
	BME_REGISTER_COMP_P7 = const(0x9A)
	BME_REGISTER_COMP_P8 = const(0x9C)
	BME_REGISTER_COMP_P9 = const(0x9E)
	BME_REGISTER_COMP_H1 = const(0xA1)
	BME_REGISTER_COMP_H2 = const(0xE1)
	BME_REGISTER_COMP_H3 = const(0xE3)
	BME_REGISTER_COMP_H4 = const(0xE4)
	BME_REGISTER_COMP_H5 = const(0xE5)
	BME_REGISTER_COMP_H6 = const(0xE6)
	BME_REGISTER_COMP_H7 = const(0xE7)

	# Control Registers
	BME_REGISTER_RESET = const(0xE0)
	BME_REGISTER_RESET_VALUE = const(0xB6)
	BME_REGISTER_CONTROL_HUM = const(0xF2)
	BME_REGISTER_STATUS = const(0xF3)
	BME_REGISTER_CONTROL = const(0xF4)
	BME_REGISTER_CONFIG = const(0xF5)

	# Sample Registers
	BME_REGISTER_SAMPLE_PRESSURE = const(0xF7)
	BME_REGISTER_SAMPLE_TEMPERATURE = const(0xFA)
	BME_REGISTER_SAMPLE_HUMIDITY = const(0xFD)

	# Default I2C Address
	BME_ADDRESS = const(0x76)

	def __init__(self, i2c=None, address=BME_ADDRESS):
		# Validate inputs
		if i2c is None:
			raise ValueError("Invalid i2c object.")
		
		self._i2c = i2c
		self._address = address
		
		if not self._read_unsigned_8(self.BME_REGISTER_CHIPID) == 0x60:
			raise Exception("Invalid BME chip ID during init.")
		
		self.reset()
		self._read_calibration()
		self.t_fine = 0
		
		self.LAST_UPDATE = 0
		self.temperature = 0
		self.humidity = 0
		self.pressure = 0
	
	def read(self):
		self.temperature = self.read_temperature()
		self.humidity = self.read_humidity()
		self.pressure = self.read_pressure()
		self.LAST_UPDATE = utime.ticks_ms()
	
	def reset(self):
		self._write_8(self.BME_REGISTER_RESET, self.BME_REGISTER_RESET_VALUE)
		
		reset_time = utime.ticks_ms()
		while(True):
			if self._check_reading_calibration() == 0:
				break
			if utime.ticks_diff(utime.ticks_ms(), reset_time) > 100:
				raise Exception("Timeout waiting for BME reset to complete.")
			utime.sleep_ms(10)
	
	def _read_status(self):
		return self._read_unsigned_8(self.BME_REGISTER_STATUS)
	
	def _check_reading_calibration(self):
		return (self._read_status() & 0x01)
	
	def start(self, mode=BME_MODE_NORMAL, temp_oversample=BME_OVERSAMPLE_X16, press_oversample=BME_OVERSAMPLE_X16, hum_oversample=BME_OVERSAMPLE_X16,
				filter=BME_FILTER_OFF, standby=BME_STANDBY_MS_0_5):
		# Put device in sleep mode first to make sure our settings are applied
		self._write_8(self.BME_REGISTER_CONTROL, self.BME_MODE_SLEEP)
		# Write our configuration registers
		self._write_8(self.BME_REGISTER_CONTROL_HUM, hum_oversample)
		self._write_8(self.BME_REGISTER_CONFIG, (((standby & 0x07) << 5) | ((filter & 0x07) << 2) | 0))
		self._write_8(self.BME_REGISTER_CONTROL, (((temp_oversample & 0x07) << 5) | ((press_oversample & 0x07) << 2) | (mode & 0x03)))

	def _read_calibration(self):
		# Temperature calibration
		self.cal_T1 = self._read_unsigned_16(self.BME_REGISTER_COMP_T1, endian="little")
		self.cal_T2 = self._read_signed_16(self.BME_REGISTER_COMP_T2, endian="little")
		self.cal_T3 = self._read_signed_16(self.BME_REGISTER_COMP_T3, endian="little")
		
		# Pressure calibration
		self.cal_P1 = self._read_unsigned_16(self.BME_REGISTER_COMP_P1, endian="little")
		self.cal_P2 = self._read_signed_16(self.BME_REGISTER_COMP_P2, endian="little")
		self.cal_P3 = self._read_signed_16(self.BME_REGISTER_COMP_P3, endian="little")
		self.cal_P4 = self._read_signed_16(self.BME_REGISTER_COMP_P4, endian="little")
		self.cal_P5 = self._read_signed_16(self.BME_REGISTER_COMP_P5, endian="little")
		self.cal_P6 = self._read_signed_16(self.BME_REGISTER_COMP_P6, endian="little")
		self.cal_P7 = self._read_signed_16(self.BME_REGISTER_COMP_P7, endian="little")
		self.cal_P8 = self._read_signed_16(self.BME_REGISTER_COMP_P8, endian="little")
		self.cal_P9 = self._read_signed_16(self.BME_REGISTER_COMP_P9, endian="little")
		
		# Humidity calibration
		self.cal_H1 = self._read_unsigned_8(self.BME_REGISTER_COMP_H1)
		self.cal_H2 = self._read_signed_16(self.BME_REGISTER_COMP_H2, endian="little")
		self.cal_H3 = self._read_unsigned_8(self.BME_REGISTER_COMP_H3)
		self.cal_H4 = (self._read_signed_8(self.BME_REGISTER_COMP_H4) << 4) | (self._read_signed_8(self.BME_REGISTER_COMP_H5) & 0xF)
		self.cal_H5 = (self._read_signed_8(self.BME_REGISTER_COMP_H6) << 4) | (self._read_signed_8(self.BME_REGISTER_COMP_H5) >> 4)
		self.cal_H6 = self._read_signed_8(self.BME_REGISTER_COMP_H7)
	
	def _read_temp_raw(self):
		return (self._read_unsigned_24(self.BME_REGISTER_SAMPLE_TEMPERATURE, endian="big") >> 4)
	
	def read_temperature(self):
		raw = self._read_temp_raw()

		var1 = (((raw >> 3) - (self.cal_T1 << 1)) * self.cal_T2) >> 11
		var2 = (((((raw >> 4) - self.cal_T1) * ((raw >> 4) - self.cal_T1)) >> 12) * self.cal_T3) >> 14

		self.t_fine = var1 + var2
		return ((self.t_fine * 5 + 128) >> 8) / 100
	
	def _read_humidity_raw(self):
		return self._read_unsigned_16(self.BME_REGISTER_SAMPLE_HUMIDITY, endian="big")
	
	def read_humidity(self):
		# Read the temperature first because the humidity calibration needs t_fine
		if self.t_fine == 0:
			self.read_temperature()
		
		raw = self._read_humidity_raw()
		hum = self.t_fine - 76800
		hum = (((((raw << 14) - (self.cal_H4 << 20) - (self.cal_H5 * hum)) + 16384) >> 15) * (((((((hum * self.cal_H6) >> 10) * ((( hum * self.cal_H3) >> 11) + 32768)) >> 10) + 2097152) * self.cal_H2 + 8192) >> 14))
		hum = hum - (((((hum >> 15) * (hum >> 15)) >> 7) * self.cal_H1) >> 4)
		if hum < 0:
			hum = 0
		if hum > 419430400:
			hum = 419430400
		return (hum >> 12) / 1024
	
	def _read_pressure_raw(self):
		return (self._read_unsigned_24(self.BME_REGISTER_SAMPLE_PRESSURE, endian="big") >> 4)
	
	def read_pressure(self):
		# Read the temperature first because the humidity calibration needs t_fine
		if self.t_fine == 0:
			self.read_temperature()
		
		raw = self._read_pressure_raw()
		
		var1 = (self.t_fine >> 1) - 64000
		var2 = (((var1 >> 2) * (var1 >> 2)) >> 11) * self.cal_P6
		var2 = var2 + ((var1 * self.cal_P5) << 1)
		var2 = (var2 >> 2) + (self.cal_P4 << 16)
		var1 = (((self.cal_P3 * (((var1 >> 2) * (var1 >> 2)) >> 13)) >> 3) + ((self.cal_P2 * var1) >> 1)) >> 18
		var1 = (((32768 + var1) * self.cal_P1) >> 15)
		if var1 == 0:
			return 0
		press = ((1048576 - raw) - (var2 >> 12)) * 3125
		press = (press << 1) // var1
		var1 = (self.cal_P9 * (((press >> 3) * (press >> 3)) >> 13)) >> 12
		var2 = ((press >> 2) * self.cal_P8) >> 13
		press = press + ((var1 + var2 + self.cal_P7) >> 4)
		return (press / 100)

	def _read_unsigned_8(self, register):
		return int.from_bytes(self._i2c.readfrom_mem(self._address, register, 1), "little") & 0xFF
	
	def _read_signed_8(self, register):
		value = self._read_unsigned_8(register)
		if value > 0x7F:
			return (value - 0x100)
		return value
	
	def _read_unsigned_16(self, register, endian="little"):
		return int.from_bytes(self._i2c.readfrom_mem(self._address, register, 2), endian) & 0xFFFF
	
	def _read_signed_16(self, register, endian="little"):
		value = self._read_unsigned_16(register, endian)
		if value > 0x7FFF:
			return (value - 0x10000)
		return value

	def _read_unsigned_24(self, register, endian="little"):
		return int.from_bytes(self._i2c.readfrom_mem(self._address, register, 3), endian) & 0xFFFFFF
	
	def _read_signed_24(self, register, endian="little"):
		value = self._read_unsigned_24(register, endian)
		if value > 0x7FFFFF:
			return (value - 0x1000000)
		return value

	def _write_8(self, register, value):
		value = value & 0xFF
		self._i2c.writeto_mem(self._address, register, value.to_bytes(1, "little"))