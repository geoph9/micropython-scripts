import time
import machine

adc = machine.ADC(0)

def do_connect():
	import network
	sta_if = network.WLAN(network.STA_IF)
	ap_if = network.WLAN(network.AP_IF)
	if (not sta_if.active()) or (not sta_if.isconnected()):
		f = open('credentials.txt', 'r')
		ssid, pwd = f.read().split(",")  # e.g "my_ssid,my_password"
		f.close()
		sta_if.active(True)
		sta_if.connect(ssid, pwd)
		while not sta_if.isconnected():
			time.sleep(5)

	if ap_if.active():
		ap_if.active(False)

def get_analog():
	vol = adc.read() * 2/1024  # convert to [0, 2]
	# return values from range(0, 1, step=0.05)
	return round(vol, 1) / 2
