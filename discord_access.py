# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 20:39:56 2023

@author: Fabian Oppliger, fabian.oppliger@epfl.ch


This program allows to send messages on a specific Discord channel. The channel URL
and access token for the specific user are defined in the config.ini file.
"""

import configparser
import logging
import requests

class Discord_access():
    def __init__(self):
        # Read config file to setup connection Discord server with the desired user
        config = configparser.ConfigParser()
        config.read('config.ini')
        config_discord = config['DISCORD']
        
        # define which discord channel to send to and the access token necessary authorization
        self.discord_channel = config_discord['channel_url']
        self.access_token = config_discord['access_token']
        self.header = {'authorization': self.access_token}
        
        #'https://discord.com/api/v9/channels/1063912811991941130/messages'
        #'MTA2MzkwNzU3NTU1MDE5MzgyNA.GVlQ4M.W2DvUjo6vsi9Tl6ODLGUTrWvSDVvmrREj2nEFg'
        
    def send_message(self,msg):
        logging.info(msg)
        payload = {'content': msg}
        # requests.post(self.discord_channel, data=payload, headers=self.header)
    
    def send_warning(self,msg):
        logging.warning(msg)
        payload = {'content': 'Warning: '+msg}
        # requests.post(self.discord_channel, data=payload, headers=self.header)
        

