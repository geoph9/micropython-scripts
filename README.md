# MicroPython Scripts

I wanted to try out alternatives for flashing C++ code to my boards (ESP8266, ESP32, Arduinos)and I thought I should try MicroPython since it is the most popular alternative. A drawback is that it is slower than C++ but I am not sure if the difference will affect me.

## Scripts

1. I am using [go-chromecast](https://github.com/vishen/go-chromecast) for controlling my Chromecast device over the command line. I recently noticed that it also offers an HTTP server and so I thought I should run it on one of my raspberry pis. 

In the sub-directory [`cast-client`](/cast-client), I have my script for controlling my chromecast device through some buttons and a potentiometer (for the volume). This is aimed to be a simple controller which will work with an esp8266 as the http client.
