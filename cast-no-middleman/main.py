import utime as time
import machine
import esp
import caster
import wificonfig
import uerrno

cast_ip = list(wificonfig.CHROMECASTS.keys())

cast_name = wificonfig.CHROMECASTS


def cycle(p):
    """
    Makes a generator cycling through arg p
    """
    try:
        len(p)
    except TypeError:
        # len() is not defined for this type. Assume it is
        # a finite iterable so we must cache the elements.
        cache = []
        for i in p:
            yield i
            cache.append(i)
        p = cache
    while p:
        yield from p


chromecast = cycle(cast_ip)

device = next(chromecast)

volume = machine.ADC(0)


def connect2device():
    """
    Connects to cast device and returns an instance of the device.
    If can't connect to the device, pops it from the cast_ip list
    and switches to the next device
    """
    global device
    connected = False
    cast = None
    while not connected:
        try:
            cast = caster.Chromecast(device)
            connected = True
        except OSError as err:
            if err.args[0] == uerrno.ECONNABORTED:
                new_device = next(chromecast)
                print('ERROR CONNECTING TO: ', cast_name[device])
                cast_ip.pop(cast_ip.index(device))
                del cast_name[device]
                device = new_device

    return cast


def get_analog_value():
    vol = volume.read() * 2 / 1024  # convert to [0, 2]
    # return values from range(0, 1, step=0.05)
    return round(vol, 1) / 2


def main():
    global device
    device = next(chromecast)
    button = machine.Pin(5, machine.Pin.IN)
    cast = connect2device()
    current_vol = cast.get_volume
    last_enc_val = current_vol
    last_change_tick = time.ticks_ms()
    print('Connected to:', cast_name[device], device, 'current vol:', current_vol)

    while True:
        val = get_analog_value()
        if last_enc_val != val:
            print(val)
            last_enc_val = val
            last_change_tick = time.ticks_ms()

        # CHANGING VOLUME
        if (time.ticks_diff(time.ticks_ms(), last_change_tick) > 200) and (last_enc_val != current_vol):
            cast.set_volume(val)
            current_vol = cast.get_volume
            print('current volume:', current_vol)

        # SLEEP AFTER DELAY
        if time.ticks_diff(time.ticks_ms(), last_change_tick) > 10000:  # 10 sec
            # cast.disconnect()
            print("SLEEP")
            # esp.deepsleep()

        # CHANGING CHROMECAST WITH ENCODER BUTTON
        if button.value():
            print('BUTTON PRESSED')
            b_start = time.ticks_ms()
            while button.value():
                if time.ticks_diff(time.ticks_ms(), b_start) > 2000:
                    print('STOPPING PLAYBACK')
                    cast.stop_playback()
                    time.sleep_ms(1500)
                    last_change_tick = time.ticks_ms()
                    break
            if time.ticks_diff(time.ticks_ms(), b_start) < 2000:
                cast.disconnect()
                prev_device = device
                device = next(chromecast)
                if device is not prev_device:
                    cast = connect2device()
                    current_vol = cast.get_volume
                    print('switched to:', cast_name[device], device, 'current vol:', current_vol)
                last_change_tick = time.ticks_ms()

        time.sleep_ms(100)


if __name__ == '__main__':
    main()
