import usocket as socket
import ussl as ssl
# import ure as re
# import utime as time
# import machine
from ustruct import unpack
import ujson as json


INIT_MSGS = (
            b'\x00\x00\x00Y\x08\x00\x12\x08sender-0\x1a\nreceiver-0"(urn:x-cast:com.google.cast.tp.connection(\x002\x13{"type": "CONNECT"}',
            b'\x00\x00\x00g\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002&{"type": "GET_STATUS", "requestId": 1}'
            )

VOL_MSGS = {
            4: b'\x00\x00\x00\x81\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002@{"type": "SET_VOLUME", "volume": {"level": ###}, "requestId": $$$}',
            5: b'\x00\x00\x00\x82\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002A{"type": "SET_VOLUME", "volume": {"level": ###}, "requestId": $$$}',
            6: b'\x00\x00\x00\x83\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002B{"type": "SET_VOLUME", "volume": {"level": ###}, "requestId": $$$}',
            7: b'\x00\x00\x00\x84\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002C{"type": "SET_VOLUME", "volume": {"level": ###}, "requestId": $$$}',
            8: b'\x00\x00\x00\x85\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002D{"type": "SET_VOLUME", "volume": {"level": ###}, "requestId": $$$}'
            }

STOP_MSGS = {
            1: b'\x00\x00\x00\x96\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002U{"type": "STOP", "requestId": $$$, "sessionId": "###"}',
            2: b'\x00\x00\x00\x97\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002V{"type": "STOP", "requestId": $$$, "sessionId": "###"}',
            3: b'\x00\x00\x00\x98\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002W{"type": "STOP", "requestId": $$$, "sessionId": "###"}'
            }

PAUSE_MSGS = {
            1: b'\x00\x00\x00\x96\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002U{"type": "PAUSE", "requestId": $$$, "sessionId": "###"}',
            2: b'\x00\x00\x00\x97\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002V{"type": "PAUSE", "requestId": $$$, "sessionId": "###"}',
            3: b'\x00\x00\x00\x98\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002W{"type": "PAUSE", "requestId": $$$, "sessionId": "###"}'
            }

PLAY_MSGS = {
            1: b'\x00\x00\x00\x96\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002U{"type": "PLAY", "requestId": $$$, "sessionId": "###"}',
            2: b'\x00\x00\x00\x97\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002V{"type": "PLAY", "requestId": $$$, "sessionId": "###"}',
            3: b'\x00\x00\x00\x98\x08\x00\x12\x08sender-0\x1a\nreceiver-0"#urn:x-cast:com.google.cast.receiver(\x002W{"type": "PLAY", "requestId": $$$, "sessionId": "###"}'
            }


class Chromecast:
    def __init__(self, ip):
        self.ip = ip
        self.vol = None
        self.player_status = None
        self.sess_id = None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.ip, 8009))  # connect ot the chromecast
        self.s = ssl.wrap_socket(self.s)
        for msg in INIT_MSGS:
            self.s.write(msg)
        self.request = 2
        # self.read_message()

    @property
    def get_volume(self):
        return self.vol

    def set_volume(self, vol):
        msg_len = len(str(vol)) + len(str(self.request))
        r_vol_msg = VOL_MSGS[msg_len]
        r_vol_msg = r_vol_msg.replace(b"###", bytes(str(vol), 'utf-8'))
        r_vol_msg = r_vol_msg.replace(b"$$$", bytes(str(self.request), 'utf-8'))
        self.s.write(r_vol_msg)
        self.request += 1
        self.read_message()

    def disconnect(self):
        self.s.close()

    def stop_playback(self):
        if self.sess_id:
            msg_size = len(str(self.request))
            stop_msg = STOP_MSGS[msg_size]
            stop_msg = stop_msg.replace(b"###", bytes(self.sess_id, 'utf-8'))
            stop_msg = stop_msg.replace(b"$$$", bytes(str(self.request), 'utf-8'))
            self.s.write(stop_msg)
            self.request += 1
            self.read_message()

    def play_playback(self):
        if self.sess_id:
            msg_size = len(str(self.request))
            play_msg = PLAY_MSGS[msg_size]
            play_msg = play_msg.replace(b"###", bytes(self.sess_id, 'utf-8'))
            play_msg = play_msg.replace(b"$$$", bytes(str(self.request), 'utf-8'))
            self.s.write(play_msg)
            self.request += 1
            self.read_message()

    def pause_playback(self):
        if self.sess_id:
            msg_size = len(str(self.request))
            pause_msg = PAUSE_MSGS[msg_size]
            pause_msg = pause_msg.replace(b"###", bytes(self.sess_id, 'utf-8'))
            pause_msg = pause_msg.replace(b"$$$", bytes(str(self.request), 'utf-8'))
            self.s.write(pause_msg)
            self.request += 1
            self.read_message()

    def read_message(self):
        size = unpack('>I', self.s.read(4))[0]
        status = str(self.s.read(size))
        d = "{" + "{".join(str(status).split("{")[1:]).replace("\'", "")
        d = json.loads(d)
        # d will look like this:
        # {'status':
        #   {'applications':
        #       [
        #           {'statusText': '', 'appId': 'XXX', 'displayName': 'XXX',
        #            'transportId': 'XXX', 'universalAppId': 'XXX',
        #            'namespaces':
        #               [
        #                   {'name': 'urn:x-cast:com.google.cast.debugoverlay'},
        #                   {'name': 'urn:x-cast:com.google.cast.cac'},
        #                   {'name': 'urn:x-cast:com.google.cast.sse'},
        #                   {'name': 'urn:x-cast:com.google.cast.remotecontrol'}
        #               ],
        #            'launchedFromCloud': False, 'iconUrl': '', 'sessionId': 'd422d80b-d58e-4cbe-ad47-31a691827e7e',
        #            'isIdleScreen': True}
        #        ],
        #        'userEq': {},
        #        'volume': {
        #           'muted': False, 'stepInterval': 0.05,
        #           'controlType': 'attenuation', 'level': 0.82
        #        }
        #    },
        #    'requestId': 1,
        #    'type': 'RECEIVER_STATUS'
        # }
        if 'status' in d.keys():
            self.vol = d['status']['volume']['level']
            # statusText: 'Casting: ' + E.g. title of the casted video
            # displayName: E.g. 'Spotify'
            self.player_status = d['status']['applications'][0]['statusText']
            self.sess_id = d['status']['applications'][0]['sessionId']
        else:
            self.vol = d['device']['volume']['level']
            self.sess_id = None
        # try:
        #     self.vol = d['status']['volume']['level']
        #     # statusText: 'Casting: ' + E.g. title of the casted video
        #     # displayName: E.g. 'Spotify'
        #     self.player_status = d['status']['applications'][0]['statusText']
        #     self.sess_id = d['status']['applications'][0]['sessionId']
        # except KeyError as ke:
        #     self.sess_id = None
        #     print("KeyError:", ke)
        #     print("d was:", d)
        #     print("\n========================================\n")
        #     print("status was:", status)
        #     pass
