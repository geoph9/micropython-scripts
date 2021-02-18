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
		play_pause = False
		try:
			# Pop it in order to avoid sending it as a query parameter
			play_pause = kwargs.pop("play_pause")
		except KeyError:
			pass
		for key, val in kwargs.items():
			self.url += "&{}={}".format(key, val)
		self.current_value = pin.value()
		self.current_time = time.time()
		if play_pause:
			self.pin.irq(trigger=Pin.IRQ_RISING, handler=self._handle_play_pause)
		else:
			self.pin.irq(trigger=Pin.IRQ_RISING, handler=self.send_req)

	def send_req(self, _):
		# Avoid consecutive requests
		if time.time() - self.current_time <= 1:  # allow only one request per second
			self.current_time = time.time()
			return True
		print("Sending request to: ", self.url)
		try:
			resp = urequests.post(self.url)
		except Exception as e:
			print("Exception while handling button event:", e)
			return False
		if resp.status_code == 200:
			return True
		return False

	def check(self):
		if self.pin.value() != self.current_value:
			return self.send_req()
		return False

	def _handle_play_pause(self, _):
		try:
			# We first need to check the current state (i.e. PLAYING OR PAUSE?)
			# If PLAYING then simply send request to /pause in order to pause the player.
			# same for the other way around
			url = re.sub(r"/pause|/unpause", "/status", self.url)
			r = urequests.get(url)
			if r.status_code == 200:
				try:
					new_action = player_state_to_action[r.json().get("player_state")]
					self.url = re.sub("status", new_action, url)
					return self.send_req(_)
				except KeyError as e:
					print("KeyError:", e)
		except Exception as e:
			print("Exception in _get_devices:", e)
		return False

