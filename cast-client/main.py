import sys
import time
import json
from machine import Pin, ADC
from handler import Connector, ButtonEvent
import urequests

volume = ADC(0)
# D1->GPIO5, D2->GPIO4, D3->GPIO0, D4->GPIO2, D5->GPIO14, 
# D6->GPIO12, D7->GPIO13, D8->GPIO15
mappings = {
    "D1": 5, "D2": 4, "D3": 0, "D4": 2, "D5": 14, "D6": 12,
    "D7": 13, "D8": 15
}

red_led = Pin(mappings["D6"], Pin.OUT)
yellow_led = Pin(mappings["D4"], Pin.OUT)

play_pause_button = Pin(mappings["D2"], Pin.IN, Pin.PULL_UP)
ffwd_button = Pin(mappings["D1"], Pin.IN, Pin.PULL_UP)
rewind_button = Pin(mappings["D5"], Pin.IN, Pin.PULL_UP)


def read_config(path):
    f = open(path, 'r')  # TODO: utf-8?
    config = json.loads(f.read())
    f.close()
    return config


def get_analog():
    vol = volume.read() * 2 / 1024  # convert to [0, 2]
    # return values from range(0, 1, step=0.05)
    return round(vol, 1) / 2


def send_post(url):
    try:
        resp = urequests.post(url)
        if resp.status_code == 200:
            return True
    except:
        # Maybe the chromecast got disconnected?
        # TODO
        pass
    return False


# TODO: Use Deep-Sleep mode in case the chromecast is not connected/does not respond
#       Connect GPIO16 (D0) to RST.
#       https://docs.micropython.org/en/latest/esp8266/tutorial/powerctrl.html#deep-sleep-mode

class Caster:
    def __init__(self, config_path="./config.json", deepsleep_timeout=1000):
        self.deepsleep_timeout = deepsleep_timeout
        self.status = True
        self.current_volume = -1
        # Read config
        self.config = read_config(config_path)
        # Connect to WIFI
        self.do_connect()
        # Connect to the chromecast device
        self.connector = Connector(base_url=self.config["server"]['base_url'])
        if not self.connector.connect():
            self.status = False
            self._deep_sleep()
        # Handlers for button events
        # TODO: Add play/pause
        self.button_events = [
            ButtonEvent(ffwd_button, self.config['server']['base_url'],
                        action='seek', uuid=self.connector.uuid,
                        seconds=10),
            ButtonEvent(rewind_button, self.config['server']['base_url'],
                        action='rewind', uuid=self.connector.uuid,
                        seconds=10)
        ]
        self.play_pause_event = ButtonEvent(play_pause_button, self.config['server']['base_url'],
                                            action='pause', uuid=self.connector.uuid, play_pause=True,
                                            playing_led_pin=yellow_led, paused_led_pin=red_led)

    def do_connect(self):
        import network
        sta_if = network.WLAN(network.STA_IF)
        ap_if = network.WLAN(network.AP_IF)
        if ap_if.active():
            ap_if.active(False)
        if (not sta_if.active()) or (not sta_if.isconnected()):
            sta_if.active(True)
            sta_if.connect(self.config['wifi']['ssid'], self.config['wifi']['pwd'])
            del self.config['wifi']  # no need to keep the credentials
            for i in range(50):
                if not sta_if.isconnected():
                    print("Could not connect to the network... Waiting for 5 seconds and retrying.")
                    time.sleep(5)
                else:
                    return
            self.status = False
            self._deep_sleep()

    def _deep_sleep(self):
        self.connector.disconnect()
        # TODO
        # sys.exit(1)
        pass

    def _handle_volume(self):
        vol = get_analog()
        if vol != self.current_volume:
            self.current_volume = vol
            url = "{}/volume?uuid={}&volume={}".format(self.config['server']['base_url'],
                                                       self.connector.uuid, vol)
            send_post(url)

    def loop(self):
        if not self.status:
            self._deep_sleep()
        print("Waiting for requests...")
        while True:
            try:
                for button in self.button_events:
                    button.check()
                self._handle_volume()
                self.play_pause_event.check_update()
                # TODO: Handle play/pause (the difficulty is that we need to know the current state
                #       so that we will be able to either hit/play or /pause)
                time.sleep(0.01)  # repeat every 50 ms
            except Exception as e:
                print("Something wrong happened while looping:", e)
                self._deep_sleep()


# Start caster
caster = Caster()
caster.loop()
