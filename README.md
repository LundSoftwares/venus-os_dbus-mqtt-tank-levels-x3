# venus-os_dbus-mqtt-tank-levels-x3 - Emulates up to 3 separate tank level sensors in VenusOS from info in MQTT data

**First off, a big thanks to [mr-manuel](https://github.com/mr-manuel) that created a bunch of templates that made this possible**

GitHub repository: [LundSoftwares/venus-os_dbus-mqtt-tank-levels-x3](https://github.com/LundSoftwares/venus-os_dbus-mqtt-tank-levels-x3)

### Disclaimer
I'm not responsible for the usage of this script. Use on own risk! 


### Purpose
The script emulates up to 3 tank level sensors in Venus OS. It gets the MQTT data from a subscribed topic and publishes the information on the dbus as the service com.victronenergy.tank.mqtt_tank_levels with the VRM instances from the Config file.


### Config
Copy or rename the config.sample.ini to config.ini in the dbus-mqtt-tank-levels folder and change it as you need it.

<details>
  
<summary>Example: Set number of instances to create, then set custom name, VRM Instance, tank capacity, type and sensor standard for all Sensors</summary>

```ruby
;How many Tank instances? 1, 2 or 3
instances = 1	

;-------------------------------------------------------------

; Device name Tank 1
; default: MQTT Tank 1
device_name = MQTT Tank 1

; Device VRM instance 1
; default: 150
device_instance = 150

; Tank 1 Capacity in m3
capacity = 0,25

; Fluid Type Tank 1
; 0=Fuel; 1=Fresh water; 2=Waste water; 3=Live well; 4=Oil; 5=Black water (sewage)
; 6=Gasoline; 7=Diesel; 8=Liquid  Petroleum Gas (LPG); 9=Liquid Natural Gas (LNG)
; 10=Hydraulic oil; 11=Raw water
; default = 0
type = 0

; Sensor Standard Tank 1
; 0=European (resistive); 1=USA (resistive); 2=Not applicable (used for Voltage and Amp sensors)
; default = 0
standard = 0

```
</details>

#### JSON structure
<details>
<summary>Minimum required</summary> 
  
```ruby
{
    "level": 90
}
```
</details>

<details>
<summary>1 tank with remaning volume</summary> 
  
```ruby
{
    "level": 90,
    "remaining": 0.225
}
```
</details>

<details>
<summary>Full</summary> 
  
```ruby
{
    "level": 90,
    "remaining": 0.225,
    "level2": 50,
    "remaining2": 0.125,
    "level3": 50,
    "remaining3": 0.125,
}
```
</details>


### Install
1. Copy the ```dbus-mqtt-tank-levels``` folder to ```/data/etc``` on your Venus OS device

2. Run ```bash /data/etc/dbus-mqtt-tank-levels/install.sh``` as root

The daemon-tools should start this service automatically within seconds.

### Uninstall
Run ```/data/etc/dbus-mqtt-tank-levels/uninstall.sh```

### Restart
Run ```/data/etc/dbus-mqtt-tank-levels/restart.sh```

### Debugging

The logs can be checked with ```tail -n 100 -F /data/log/dbus-mqtt-tank-levels/current | tai64nlocal```

The service status can be checked with svstat: ```svstat /service/dbus-mqtt-tank-levels```

This will output somethink like ```/service/dbus-mqtt-tank-levels: up (pid 5845) 185 seconds```

If the seconds are under 5 then the service crashes and gets restarted all the time. If you do not see anything in the logs you can increase the log level in ```/data/etc/dbus-mqtt-tank-levels/dbus-mqtt-tank-levels.py``` by changing ```level=logging.WARNING``` to ```level=logging.INFO``` or ```level=logging.DEBUG```

If the script stops with the message ```dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.tank.mqtt_tank_levels"``` it means that the service is still running or another service is using that bus name.

### Compatibility
Tested with Venus OS Large ```v3.40``` on the following devices:

- RaspberryPi 4
- Real Sensor data sent from NodeRed

### NodeRed Example code

<details>
<summary>Import into NodeRed runing on your VenusOS device for some simple testing</summary> 
  
```ruby
[{"id":"9b8c640eb36eca97","type":"mqtt out","z":"36b8e7c267cde307","name":"MQTT out","topic":"Tank/Levels","qos":"","retain":"","respTopic":"","contentType":"","userProps":"","correl":"","expiry":"","broker":"3cc159c0642d9663","x":720,"y":460,"wires":[]},{"id":"25b4ff51ccfe4cce","type":"function","z":"36b8e7c267cde307","name":"function 3","func":"msg.payload=\n{\n    \"level\": 90,\n    \"remaining\": 0.225,\n    \"level2\": 50,\n    \"remaining2\": 0.125,\n}\nreturn msg;","outputs":1,"noerr":0,"initialize":"","finalize":"","libs":[],"x":520,"y":460,"wires":[["9b8c640eb36eca97"]]},{"id":"fa09c9bc13a91df8","type":"inject","z":"36b8e7c267cde307","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"30","crontab":"","once":true,"onceDelay":"1","topic":"","payload":"","payloadType":"date","x":350,"y":460,"wires":[["25b4ff51ccfe4cce"]]},{"id":"3cc159c0642d9663","type":"mqtt-broker","name":"","broker":"localhost","port":"1883","clientid":"","autoConnect":true,"usetls":false,"protocolVersion":"4","keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","birthMsg":{},"closeTopic":"","closeQos":"0","closePayload":"","closeMsg":{},"willTopic":"","willQos":"0","willPayload":"","willMsg":{},"userProps":"","sessionExpiry":""}]
```
</details>


### Screenshots

<details>
<summary>Device List</summary> 
  
![1](https://github.com/LundSoftwares/venus-os_dbus-mqtt-tank-levels-x2/assets/23386303/1d9bf991-7472-47b7-9f44-7c4cbb05b6c1)


</details>

<details>
<summary>Device Status</summary> 
  
![2](https://github.com/LundSoftwares/venus-os_dbus-mqtt-tank-levels-x2/assets/23386303/e8be1d03-cf5a-48d1-a71d-b635a7962ae1)


</details>

<details>
<summary>Device Settings</summary> 
  
![3](https://github.com/LundSoftwares/venus-os_dbus-mqtt-tank-levels-x2/assets/23386303/e8f31ab5-33e7-40e6-a500-878b6fd4569d)


</details>

<details>
<summary>Front Page</summary> 
  
![4](https://github.com/LundSoftwares/venus-os_dbus-mqtt-tank-levels-x2/assets/23386303/e1d10304-e5c2-4f4c-8a9d-327c84a52f15)


</details>



# Sponsor this project

<a href="https://www.paypal.com/donate/?business=MTXQ49TG6YH36&no_recurring=0&item_name=Like+my+work?+%0APlease+buy+me+a+coffee...&currency_code=SEK">
  <img src="https://pics.paypal.com/00/s/MjMyYjAwMjktM2NhMy00NjViLTg3N2ItMDliNjY3MjhiOTJk/file.PNG" alt="Donate with PayPal" />
</a>
