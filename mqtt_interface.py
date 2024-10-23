# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 20:39:56 2023

@author: Fabian Oppliger, fabian.oppliger@epfl.ch


The Client_bftc class sets up an MQTT connection to a Bluefors temperature controller
API and allows to subscribe to a channel and periodically receive temperature readings.
The monitor_temp function runs in a loop until the specified temperature threshold
is reached. The IP address of the API is defined in the config.ini file.
"""

import time
import json
import configparser
import paho.mqtt.client as mqtt

class Client_bftc(mqtt.Client):
    def __init__(self):
        # Read config file to setup connection to API
        config = configparser.ConfigParser()
        config.read('config.ini')
        config_mqtt = config['MQTT']
        
        # define mqtt client and connect to it
        mqtt.Client.__init__(self)
        self.hostname = config_mqtt['hostname']
        self.port = int(config_mqtt['port'])
        self.temp_topic = config_mqtt['topic']
        self.threshold_reached = False

        # Connect to the broker
        self.connect(self.hostname, self.port, 60)
        
    # This function is automatically run whenever a message is sent on the 
    # subscribed topic. It reads the temperature and closes the connection
    # when the given temperature threshold is reached on the desired channel.
    def on_msg(self,client, userdata, msg):
        data = json.loads(msg.payload)
        self.time_threshold_reached = False
        if (data['channel_nr'] == self.temp_channel) & bool(data['temperature']):
            # ^ is the xor operator
            if self.cooling_bool ^ (data['temperature'] > self.temp_threshold):
                # Set boolean to True to recognize unwanted disconnections
                self.threshold_reached = True
                self.disconnect()
            # Check if the time threshold is reached. Does nothing if time_threshold is 0.
            elif self.time_threshold:
                if abs(time.time() - self.monitor_start_time) > self.time_threshold:
                    self.time_threshold_reached = True
                    self.disconnect()
    
    # First reconnects to the client, passes function arguments as object attributes
    # (otherwise, we cannot send them the the on_msg function) and then subscribes
    # to the temperature sensors and loops until the client is disconnected 
    # (which happens when the temperature theshold is reached).
    def monitor_temp(self,channel,threshold,cooling,time_threshold=0):
        self.reconnect()
        self.on_message = self.on_msg
        self.temp_channel = channel
        self.temp_threshold = threshold
        self.cooling_bool = cooling
        self.threshold_reached = False
        self.monitor_start_time = time.time()
        self.time_threshold = time_threshold
        self.subscribe(self.temp_topic,0)
        self.loop_forever()
    
    # Callback functions
    # Uncomment these two functions to test if the connection to the MQTT server works.
    # def on_connect(self,client, userdata, flags, rc):
    #     if rc == 0:
    #         print("Connected successfully to the Temperature Controller API")
    #     else:
    #         print("Connect returned result code: " + str(rc))
    
    # def on_disconnect(self,client, userdata, rc):
    #     print("Disconnected with result code "+str(rc))


