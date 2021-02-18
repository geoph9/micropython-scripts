# MicroPython Scripts

I wanted to try out alternatives for flashing C++ code to my boards (ESP8266, ESP32, Arduinos)and I thought I should try 
MicroPython since it is the most popular alternative. A drawback is that it is slower than C++ but I am not sure if the difference will affect me.

## Scripts/Projects

### Chromecast Utils

#### Description

I am using [go-chromecast](https://github.com/vishen/go-chromecast) for controlling my Chromecast device over the command line. 
I recently noticed that it also offers an HTTP server and so I thought I should run it on one of my raspberry pis. 

In the sub-directory [`cast-client`](/cast-client), I have my script for controlling my chromecast device through some buttons 
and a potentiometer (for the volume). This is aimed to be a simple controller which will work with an esp8266 as the http client.

#### Setup

Before setting up the pins, one needs to connect the esp8266 to the WiFi. For the credentials, I am using the 
`config.json` file which contains the keys `ssid` and `pwd`. These values are read and a connection is established.

In addition to the wifi credentials, the config file also contains the endpoint of the `go-chromecast` server.

#### Connecting to the Device

After successfully connecting to the network and defining the go-chromecast endpoint, we now have to connect to the 
`go-chromecast` server and specify our Chromecast device.

This is done by hitting the `/connect` endpoint and providing it with the uuid, the address and the port where the 
chromecast device is running. The process has been automated and these are found by using the `/devices` endpoint which 
lists all of the available Chromecast devices running on your network. By default, the first chromecast device is taken 
but maybe I should add this choice in the config file so that it will be easier to change it later in case more than 
one devices run on one network.

#### Sending Requests

Now the only thing that is left to do is assign our button pins and the potentiometer to their corresponding endpoints.
For example, assign the potentiometer to the `/volume` endpoint.

All requests to the http server are sent using the `uuid=` query parameter (following by the device uuid).

### Orchestrator

A class named `Caster` is responsible for all the above. For convenience, I am also using two other classes: 

- `Connector`: A connector to the Chromecast device.
- `ButtonEvent`: Handles the requests that need to be made after a button press.

By initializing a `Caster` instance we are connecting to the network and the chromecast. Then, the only thing left to 
do is loop for eternity and wait for button requests.
