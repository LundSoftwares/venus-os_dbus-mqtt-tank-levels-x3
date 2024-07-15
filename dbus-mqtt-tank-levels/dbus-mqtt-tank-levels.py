#!/usr/bin/env python

from gi.repository import GLib  # pyright: ignore[reportMissingImports]
import platform
import logging
import sys
import os
from time import sleep, time
import json
import paho.mqtt.client as mqtt
import configparser  # for config/ini file
import _thread
import dbus

# import Victron Energy packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "ext", "velib_python"))
from vedbus import VeDbusService


class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)

class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)
        
def dbusconnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()

# get values from config.ini file
try:
    config_file = (os.path.dirname(os.path.realpath(__file__))) + "/config.ini"
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        if config["MQTT"]["broker_address"] == "IP_ADDR_OR_FQDN":
            print(
                'ERROR:The "config.ini" is using invalid default values like IP_ADDR_OR_FQDN. The driver restarts in 60 seconds.'
            )
            sleep(60)
            sys.exit()
    else:
        print(
            'ERROR:The "'
            + config_file
            + '" is not found. Did you copy or rename the "config.sample.ini" to "config.ini"? The driver restarts in 60 seconds.'
        )
        sleep(60)
        sys.exit()

except Exception:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    file = exception_traceback.tb_frame.f_code.co_filename
    line = exception_traceback.tb_lineno
    print(
        f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
    )
    print("ERROR:The driver restarts in 60 seconds.")
    sleep(60)
    sys.exit()


# Get logging level from config.ini
# ERROR = shows errors only
# WARNING = shows ERROR and warnings
# INFO = shows WARNING and running functions
# DEBUG = shows INFO and data/values
if "DEFAULT" in config and "logging" in config["DEFAULT"]:
    if config["DEFAULT"]["logging"] == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    elif config["DEFAULT"]["logging"] == "INFO":
        logging.basicConfig(level=logging.INFO)
    elif config["DEFAULT"]["logging"] == "ERROR":
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.WARNING)


# get timeout
if "DEFAULT" in config and "timeout" in config["DEFAULT"]:
    timeout = int(config["DEFAULT"]["timeout"])
else:
    timeout = 60


# get type Tank #1
if "DEFAULT" in config and "type" in config["DEFAULT"]:
    type = int(config["DEFAULT"]["type"])
else:
    type = 0

# get type Tank #2
if "DEFAULT" in config and "type2" in config["DEFAULT"]:
    type2 = int(config["DEFAULT"]["type2"])
else:
    type2 = 0

# get type Tank #3
if "DEFAULT" in config and "type3" in config["DEFAULT"]:
    type3 = int(config["DEFAULT"]["type3"])
else:
    type3 = 0

# get capacity Tank #1
if "DEFAULT" in config and "capacity" in config["DEFAULT"]:
    capacity = float(config["DEFAULT"]["capacity"])
else:
    capacity = 100

# get capacity Tank #2
if "DEFAULT" in config and "capacity2" in config["DEFAULT"]:
    capacity2 = float(config["DEFAULT"]["capacity2"])
else:
    capacity2 = 100

# get capacity Tank #3
if "DEFAULT" in config and "capacity3" in config["DEFAULT"]:
    capacity3 = float(config["DEFAULT"]["capacity3"])
else:
    capacity3 = 100
    
# get standard Tank #1
if "DEFAULT" in config and "standard" in config["DEFAULT"]:
    standard = int(config["DEFAULT"]["standard"])
else:
    standard = 0    

# get standard Tank #2
if "DEFAULT" in config and "standard2" in config["DEFAULT"]:
    standard2 = int(config["DEFAULT"]["standard2"])
else:
    standard2 = 0  

# get standard Tank #3
if "DEFAULT" in config and "standard3" in config["DEFAULT"]:
    standard3 = int(config["DEFAULT"]["standard3"])
else:
    standard3 = 0 
    
# set variables
connected = 0

last_changed = 0
last_updated = 0
level = -999
remaining = None

last_changed2 = 0
last_updated2 = 0
level2 = -999
remaining2 = None

last_changed3 = 0
last_updated3 = 0
level3 = -999
remaining3 = None

# MQTT requests
def on_disconnect(client, userdata, rc):
    global connected
    logging.warning("MQTT client: Got disconnected")
    if rc != 0:
        logging.warning(
            "MQTT client: Unexpected MQTT disconnection. Will auto-reconnect"
        )
    else:
        logging.warning("MQTT client: rc value:" + str(rc))

    while connected == 0:
        try:
            logging.warning("MQTT client: Trying to reconnect")
            client.connect(config["MQTT"]["broker_address"])
            connected = 1
        except Exception as err:
            logging.error(
                f"MQTT client: Error in retrying to connect with broker ({config['MQTT']['broker_address']}:{config['MQTT']['broker_port']}): {err}"
            )
            logging.error("MQTT client: Retrying in 15 seconds")
            connected = 0
            sleep(15)


def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        logging.info("MQTT client: Connected to MQTT broker!")
        connected = 1
        client.subscribe(config["MQTT"]["topic"])
    else:
        logging.error("MQTT client: Failed to connect, return code %d\n", rc)


def on_message(client, userdata, msg):
    try:
        global last_changed, level, remaining, last_changed2, level2, remaining2, last_changed3, level3, remaining3

        # get JSON from topic
        if msg.topic == config["MQTT"]["topic"]:
            logging.info("MQTT payload: " + str(msg.payload)[1:])
            if msg.payload != "" and msg.payload != b"":
                jsonpayload = json.loads(msg.payload)

                if "level" in jsonpayload or "value" in jsonpayload:
                    last_changed = int(time())
                    if "level" in jsonpayload:
                        level = float(jsonpayload["level"])
                    elif "value" in jsonpayload:
                        level = float(jsonpayload["value"])

                    # check if remaining exists
                    if "remaining" in jsonpayload:
                        remaining = float(jsonpayload["remaining"])
              
                    if "level2" in jsonpayload:
                        last_changed2 = int(time())
                        level2 = float(jsonpayload["level2"])
                        
                    # check if remaining2 exists
                    if "remaining2" in jsonpayload:
                        remaining2 = float(jsonpayload["remaining2"])

                    if "level3" in jsonpayload:
                        last_changed3 = int(time())
                        level3 = float(jsonpayload["level3"])
                        
                    # check if remaining3 exists
                    if "remaining3" in jsonpayload:
                        remaining3 = float(jsonpayload["remaining3"])

                else:
                    logging.error(
                        'Received JSON MQTT message does not include a level object. Expected at least: {"level": 22.0} or {"value": 22.0}'
                    )
                    logging.debug("MQTT payload: " + str(msg.payload)[1:])
                    
            else:
                logging.warning(
                    "Received JSON MQTT message was empty and therefore it was ignored"
                )
                logging.debug("MQTT payload: " + str(msg.payload)[1:])

    except ValueError as e:
        logging.error("Received message is not a valid JSON. %s" % e)
        logging.debug("MQTT payload: " + str(msg.payload)[1:])

    except Exception as e:
        logging.error("Exception occurred: %s" % e)
        logging.debug("MQTT payload: " + str(msg.payload)[1:])


class DbusMqttLevelService:
    def __init__(
        self,
        servicename,
        deviceinstance,
        paths,
        productname="MQTT Tank Levels",
        customname="MQTT Tank Levels",
        connection="MQTT Tank Levels service",
    ):
        self._dbusservice = VeDbusService(servicename,dbusconnection())
        self._paths = paths

        logging.info("Starting DbusMqttLevelService")
        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion",
            "Unkown version, and running on Python " + platform.python_version(),
        )
        self._dbusservice.add_path("/Mgmt/Connection", connection)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", deviceinstance)
        self._dbusservice.add_path("/ProductId", 0xFFFF)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path("/CustomName", customname)
        self._dbusservice.add_path("/FirmwareVersion", "0.0.2 (20240715)")
        # self._dbusservice.add_path('/HardwareVersion', '')
        self._dbusservice.add_path("/Connected", 1)

        self._dbusservice.add_path("/Status", 0)
        self._dbusservice.add_path("/FluidType", type)
        self._dbusservice.add_path("/Capacity", capacity)
        self._dbusservice.add_path("/Standard", standard)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path,
                settings["initial"],
                gettextcallback=settings["textformat"],
                writeable=True,
                onchangecallback=self._handlechangedvalue,
            )

        GLib.timeout_add(1000, self._update)  # pause 1000ms before the next request

    def _update(self):
        global last_changed, last_updated

        now = int(time())

        if last_changed != last_updated:
            self._dbusservice["/Level"] = (
                round(level, 1) if level is not None else None
            )
            self._dbusservice["/Remaining"] = (
                round(remaining, 3) if remaining is not None else None
            )

            log_message = "Level: {:.1f} %".format(level)
            log_message += (
                " - Remaining: {:.1f} m3".format(remaining) if remaining is not None else ""
            )
            logging.info(log_message)

            last_updated = last_changed

        # quit driver if timeout is exceeded
        if timeout != 0 and (now - last_changed) > timeout:
            logging.error(
                "Driver stopped. Timeout of %i seconds exceeded, since no new MQTT message was received in this time."
                % timeout
            )
            sys.exit()

        # increment UpdateIndex - to show that new data is available
        index = self._dbusservice["/UpdateIndex"] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
        self._dbusservice["/UpdateIndex"] = index
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


class DbusMqttLevelService2:
    def __init__(
        self,
        servicename,
        deviceinstance,
        paths,
        productname="MQTT Tank Levels 2",
        customname="MQTT Tank Levels 2",
        connection="MQTT Tank Levels Service 2",
    ):
        self._dbusservice = VeDbusService(servicename,dbusconnection())
        self._paths = paths

        logging.info("Starting DbusMqttLevelService2")
        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion",
            "Unkown version, and running on Python " + platform.python_version(),
        )
        self._dbusservice.add_path("/Mgmt/Connection", connection)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", deviceinstance)
        self._dbusservice.add_path("/ProductId", 0xFFFF)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path("/CustomName", customname)
        self._dbusservice.add_path("/FirmwareVersion", "0.0.2 (20240715)")
        # self._dbusservice.add_path('/HardwareVersion', '')
        self._dbusservice.add_path("/Connected", 1)

        self._dbusservice.add_path("/Status", 0)
        self._dbusservice.add_path("/FluidType", type2)
        self._dbusservice.add_path("/Capacity", capacity2)
        self._dbusservice.add_path("/Standard", standard2)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path,
                settings["initial"],
                gettextcallback=settings["textformat"],
                writeable=True,
                onchangecallback=self._handlechangedvalue,
            )

        GLib.timeout_add(1000, self._update)  # pause 1000ms before the next request

    def _update(self):
        global last_changed2, last_updated2

        now = int(time())

        if last_changed2 != last_updated2:
            self._dbusservice["/Level"] = (
                round(level2, 1) if level2 is not None else None
            )
            self._dbusservice["/Remaining"] = (
                round(remaining2, 3) if remaining2 is not None else None
            )

            log_message = "Level2: {:.1f} %".format(level2)
            log_message += (
                " - Remaining2: {:.1f} m3".format(remaining2) if remaining2 is not None else ""
            )
            logging.info(log_message)

            last_updated2 = last_changed2

        # increment UpdateIndex - to show that new data is available
        index = self._dbusservice["/UpdateIndex"] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
        self._dbusservice["/UpdateIndex"] = index
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change
    
class DbusMqttLevelService3:
    def __init__(
        self,
        servicename,
        deviceinstance,
        paths,
        productname="MQTT Tank Levels 3",
        customname="MQTT Tank Levels 3",
        connection="MQTT Tank Levels Service 3",
    ):
        self._dbusservice = VeDbusService(servicename,dbusconnection())
        self._paths = paths

        logging.info("Starting DbusMqttLevelService3")
        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion",
            "Unkown version, and running on Python " + platform.python_version(),
        )
        self._dbusservice.add_path("/Mgmt/Connection", connection)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", deviceinstance)
        self._dbusservice.add_path("/ProductId", 0xFFFF)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path("/CustomName", customname)
        self._dbusservice.add_path("/FirmwareVersion", "0.0.2 (20240715)")
        # self._dbusservice.add_path('/HardwareVersion', '')
        self._dbusservice.add_path("/Connected", 1)

        self._dbusservice.add_path("/Status", 0)
        self._dbusservice.add_path("/FluidType", type3)
        self._dbusservice.add_path("/Capacity", capacity3)
        self._dbusservice.add_path("/Standard", standard3)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path,
                settings["initial"],
                gettextcallback=settings["textformat"],
                writeable=True,
                onchangecallback=self._handlechangedvalue,
            )

        GLib.timeout_add(1000, self._update)  # pause 1000ms before the next request

    def _update(self):
        global last_changed3, last_updated3

        now = int(time())

        if last_changed3 != last_updated3:
            self._dbusservice["/Level"] = (
                round(level3, 1) if level3 is not None else None
            )
            self._dbusservice["/Remaining"] = (
                round(remaining3, 3) if remaining3 is not None else None
            )

            log_message = "Level3: {:.1f} %".format(level3)
            log_message += (
                " - Remaining3: {:.1f} m3".format(remaining3) if remaining3 is not None else ""
            )
            logging.info(log_message)

            last_updated3 = last_changed3

        # increment UpdateIndex - to show that new data is available
        index = self._dbusservice["/UpdateIndex"] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
        self._dbusservice["/UpdateIndex"] = index
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change

def main():
    _thread.daemon = True  # allow the program to quit

    from dbus.mainloop.glib import (  # pyright: ignore[reportMissingImports]
        DBusGMainLoop,
    )

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    # MQTT setup
    client = mqtt.Client("MqttLevel_" + str(config["MQTT"]["device_instance"]))
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.on_message = on_message

    # check tls and use settings, if provided
    if "tls_enabled" in config["MQTT"] and config["MQTT"]["tls_enabled"] == "1":
        logging.info("MQTT client: TLS is enabled")

        if (
            "tls_path_to_ca" in config["MQTT"]
            and config["MQTT"]["tls_path_to_ca"] != ""
        ):
            logging.info(
                'MQTT client: TLS: custom ca "%s" used'
                % config["MQTT"]["tls_path_to_ca"]
            )
            client.tls_set(config["MQTT"]["tls_path_to_ca"], tls_version=2)
        else:
            client.tls_set(tls_version=2)

        if "tls_insecure" in config["MQTT"] and config["MQTT"]["tls_insecure"] != "":
            logging.info(
                "MQTT client: TLS certificate server hostname verification disabled"
            )
            client.tls_insecure_set(True)

    # check if username and password are set
    if (
        "username" in config["MQTT"]
        and "password" in config["MQTT"]
        and config["MQTT"]["username"] != ""
        and config["MQTT"]["password"] != ""
    ):
        logging.info(
            'MQTT client: Using username "%s" and password to connect'
            % config["MQTT"]["username"]
        )
        client.username_pw_set(
            username=config["MQTT"]["username"], password=config["MQTT"]["password"]
        )

    # connect to broker
    logging.info(
        f"MQTT client: Connecting to broker {config['MQTT']['broker_address']} on port {config['MQTT']['broker_port']}"
    )
    client.connect(
        host=config["MQTT"]["broker_address"], port=int(config["MQTT"]["broker_port"])
    )
    client.loop_start()

    # wait to receive first data, else the JSON is empty and phase setup won't work
    i = 0
    while level == -999:
        if i % 12 != 0 or i == 0:
            logging.info("Waiting 5 seconds for receiving first data...")
        else:
            logging.warning(
                "Waiting since %s seconds for receiving first data..." % str(i * 5)
            )
        sleep(5)
        i += 1

    # formatting
    def _litres(p, v):
        return str("%.3f" % v) + "m3"

    def _percent(p, v):
        return str("%.1f" % v) + "%"

    def _n(p, v):
        return str("%i" % v)

    paths_dbus = {
        "/Level": {"initial": None, "textformat": _percent},
        "/Remaining": {"initial": None, "textformat": _litres},
        "/UpdateIndex": {"initial": 0, "textformat": _n},
    }

    DbusMqttLevelService(
        servicename="com.victronenergy.tank.mqtt_tank_levels_"
        + str(config["MQTT"]["device_instance"]),
        deviceinstance=int(config["MQTT"]["device_instance"]),
        customname=config["MQTT"]["device_name"],
        paths=paths_dbus,
    )

    if int(config["DEFAULT"]["instances"]) > 1 :
        DbusMqttLevelService2(
            servicename="com.victronenergy.tank.mqtt_tank_levels_"
            + str(config["MQTT"]["device_instance2"]),
            deviceinstance=int(config["MQTT"]["device_instance2"]),
            customname=config["MQTT"]["device_name2"],
            paths=paths_dbus,
        )
    
    if int(config["DEFAULT"]["instances"]) > 2 :
        DbusMqttLevelService3(
            servicename="com.victronenergy.tank.mqtt_tank_levels_"
            + str(config["MQTT"]["device_instance3"]),
            deviceinstance=int(config["MQTT"]["device_instance3"]),
            customname=config["MQTT"]["device_name3"],
            paths=paths_dbus,
        )
    
    logging.info(
        "Connected to dbus and switching over to GLib.MainLoop() (= event based)"
    )
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
