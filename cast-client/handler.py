import time
import urequests
import re
from machine import Pin


class Connector:
	def __init__(self, base_url):
		self.base_url = base_url
		self.uuid = None
		self.addr = None
		self.port = None
		self.connected = False

	def _get_devices(self):
		try:
			r = urequests.get("{}/devices".format(self.base_url))
		except Exception as e:
			print("Exception in _get_devices:", e)
			return False
		if r.status_code == 200:
			r = r.json()[0]  # use the first chromecast device (TODO: Maybe change?)
			self.uuid = r['uuid']
			self.addr = r['addr']
			self.port = r['port']
			return True
		return False

	def _connect_single(self):
		if self._get_devices():
			try:
				r = urequests.post("{}/connect?uuid={}&addr={}&port={}".format(self.base_url, self.uuid, self.addr, self.port))
				if r.status_code == 200:
					self.connected = True
					return True
			except Exception as e:
				print("Exception while connecting to the chromecast device:", e)
				return False
		return False

	def connect(self):
		for i in range(10):
			status = self._connect_single()
			if status:
				print("Successfully connected to the device...")
				return True
			print("Could not connect to your device... Trying to disconnect and then retrying")
			self.disconnect()
			time.sleep(5)  # also wait for 5 seconds
		return False

	def disconnect(self):
		try:
			r = urequests.post("{}/disconnect?uuid={}".format(self.base_url, self.uuid))
			if r.status_code == 200 or r.text.startswith("device uuid is not connected"):  # disconnected successfully
				self.connected = False
				return
		except Exception as e:
			print("Exception while disconnecting:", e)


player_state_to_action = {
	"PLAYING": "pause",
	"PAUSED": "unpause"
}


class ButtonEvent:
	def __init__(self, pin, base_url, action, uuid, **kwargs):
		self.pin = pin
		self.url = "{}/{}?uuid={}".format(base_url, action, uuid)
		play_pause = kwargs.get("play_pause", False)
		if "play_pause" in kwargs.keys():
			kwargs.pop("play_pause")
		self.paused_led_pin, self.playing_led_pin = None, None
		try:
			# Pop it in order to avoid sending it as a query parameter
			self.playing_led_pin = kwargs.pop("playing_led_pin")
			self.paused_led_pin = kwargs.pop("paused_led_pin")
			self.handler = self._handle_play_pause
		except KeyError:
			self.handler = self.send_req
			pass
		for key, val in kwargs.items():
			self.url += "&{}={}".format(key, val)
		self.current_value = pin.value()
		self.current_time = time.time()
		# if play_pause:
		# 	self.pin.irq(trigger=Pin.IRQ_RISING, handler=self._handle_play_pause)
		# else:
		# 	self.pin.irq(trigger=Pin.IRQ_RISING, handler=self.send_req)

	def send_req(self, _):
		# Avoid consecutive requests
		if time.time() - self.current_time <= 2:  # allow only one request per 2 seconds
			self.current_time = time.time()
			return
		self.current_time = time.time()
		print("Sending request to: ", self.url)
		try:
			resp = urequests.post(self.url)
		except Exception as e:
			print("Exception while handling button event:", e)
			return
		if resp.status_code == 200:
			return
		return

	def check(self):
		if self.pin.value() != self.current_value:
			self.current_value = self.pin.value()  # TODO: Remove 2nd call to value()
			return self.handler(None)
		return False

	def check_update(self):
		out = self.check()
		if time.time() - self.current_time >= 30:  # Update the LEDs every 30 seconds
			self.update_state()
			self.current_time = time.time()
		return out

	def update_state(self):
		try:
			# We first need to check the current state (i.e. PLAYING OR PAUSE?)
			# If PLAYING then simply send request to /pause in order to pause the player.
			# same for the other way around
			url = re.sub(r"/pause|/unpause", "/status", self.url)
			r = urequests.get(url)
			if r.status_code == 200:
				state = r.json().get("player_state")
				new_action = player_state_to_action.get(state, None)
				if new_action is None:
					return   # in case where the chromecast is not playing anything
				self.playing_led_pin.off()
				self.paused_led_pin.off()
				getattr(self, "{}_led_pin".format(state.lower())).on()
				self.url = re.sub("status", new_action, url)
		except Exception as e:
			print("Exception in update_state:", e)
			return False
		return True

	def _handle_play_pause(self, _):
		if self.update_state():
			self.send_req(_)

