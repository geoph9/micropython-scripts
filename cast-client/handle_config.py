import json
import time
from machine import Pin
import urequests



class Connector:
	def __init__(self, base_url):
		self.base_url = base_url
		self.uuid = None
		self.addr = None
		self.port = None

	def _get_devices(self):
		try:
			r = urequests.get("{}/devices".format(base_url))
		except:
			return False
		if r.status_code == "200":
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
			except:
				return False
			if r.status_code == "200":
				return True
		return False

	def connect(self):
		for i in range(10):
			status = self._connect_single()
			if status:
				return True
			print("Could not connect... Waiting for 5 second and then retrying")
			time.sleep(5)
		return False

class ButtonEvent():
	def __init__(self, pin, base_url, action, uuid, **kwargs):
		self.pin = pin
		self.url = "{}/{}?uuid={}".format(base_url, action, uuid)
		for key, val in kwargs.items():
			self.url += "&{}={}".format(key, val)
		self.current_value = pin.value()

	def _send_req(self):
		try:
			resp = urequests.post(self.url)
		except:
			return False
		if resp.status_code == "200":
			return True
		return False

	def check(self):
		if pin.value() != self.current_value:
			return self._send_req()
		return False

