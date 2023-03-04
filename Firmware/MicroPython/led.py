import machine
import uasyncio

class led:
	# Colors
	RED = [0, 1023, 1023]
	GREEN = [1023, 0, 1023]
	BLUE = [1023, 1023, 0]
	ORANGE = [0, 800, 1023]
	YELLOW = [0, 500, 1023]
	PURPLE = [0, 1023, 500]
	TEAL = [1023, 0, 300]
	WHITE = [0, 0, 0]
	BLACK = [1023, 1023, 1023]
	
	_gpio_red = 25
	_gpio_grn = 26
	_gpio_blu = 27
	
	def __init__(self):
		self._pwm_red = machine.PWM(machine.Pin(self._gpio_red, machine.Pin.OUT), freq=5000, duty=1023)
		self._pwm_grn = machine.PWM(machine.Pin(self._gpio_grn, machine.Pin.OUT), freq=5000, duty=1023)
		self._pwm_blu = machine.PWM(machine.Pin(self._gpio_blu, machine.Pin.OUT), freq=5000, duty=1023)
		
		self.color = self.BLACK
		self.blink = False
		self._blink_state = False
		self.on_time = 100
		self.off_time = 900

	async def run(self):
		while True:
			if not self.blink:
				self._pwm_red.duty(self.color[0])
				self._pwm_grn.duty(self.color[1])
				self._pwm_blu.duty(self.color[2])
				await uasyncio.sleep_ms(500)
			else:
				if not self._blink_state:
					self._pwm_red.duty(self.color[0])
					self._pwm_grn.duty(self.color[1])
					self._pwm_blu.duty(self.color[2])
					self._blink_state = True
					await uasyncio.sleep_ms(self.on_time)
				else:
					self._pwm_red.duty(self.BLACK[0])
					self._pwm_grn.duty(self.BLACK[1])
					self._pwm_blu.duty(self.BLACK[2])
					self._blink_state = False
					await uasyncio.sleep_ms(self.off_time)

	def step(self):
		if not self.blink:
			self._pwm_red.duty(self.color[0])
			self._pwm_grn.duty(self.color[1])
			self._pwm_blu.duty(self.color[2])
		else:
			if not self._blink_state:
				self._pwm_red.duty(self.color[0])
				self._pwm_grn.duty(self.color[1])
				self._pwm_blu.duty(self.color[2])
				self._blink_state = True
			else:
				self._pwm_red.duty(self.BLACK[0])
				self._pwm_grn.duty(self.BLACK[1])
				self._pwm_blu.duty(self.BLACK[2])
				self._blink_state = False