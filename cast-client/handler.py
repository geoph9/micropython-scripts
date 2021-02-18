import time
import urequests


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


class ButtonEvent:
	def __init__(self, pin, base_url, action, uuid, **kwargs):
		self.pin = pin
		self.url = "{}/{}?uuid={}".format(base_url, action, uuid)
		for key, val in kwargs.items():
			self.url += "&{}={}".format(key, val)
		self.current_value = pin.value()

	def _send_req(self):
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
			return self._send_req()
		return False
