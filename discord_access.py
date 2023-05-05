# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 20:39:56 2023

@author: Fabian Oppliger, fabian.oppliger@epfl.ch


This file defines a class that allows to send messages on a specific Discord
channel. The messages are also written in a logfile. The channel URL and
access token for the specific user are defined in the config.ini file.
"""

import configparser
import logs
import requests

class Discord_access():
    def __init__(self):
        # Read config file to setup connection Discord server with the desired user
        config = configparser.ConfigParser()
        config.read('config.ini')
        config_discord = config['DISCORD']
        
        # Define which discord channel to send to and the access token necessary authorization
        self.discord_channel = config_discord['channel_url']
        self.access_token = config_discord['access_token']
        self.header = {'authorization': self.access_token}
        
    # Write message in log file and on discord server
    def send_message(self,msg):
        logs.info(msg)
        payload = {'content': msg}
        requests.post(self.discord_channel, data=payload, headers=self.header)
    
    # Write warning in log file and on discord server
    def send_warning(self,msg):
        logs.warning(msg)
        payload = {'content': 'Warning: '+msg}
        requests.post(self.discord_channel, data=payload, headers=self.header)
        

