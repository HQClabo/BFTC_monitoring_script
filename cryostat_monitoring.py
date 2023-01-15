# -*- coding: utf-8 -*-
"""
Created on Sat Dec 31 01:38:18 2022

@author: Fabian Oppliger, fabian.oppliger@epfl.ch
version: 1.0

Main program that contains a simple user interface and controls which temperatures
are monitored and when messages are sent to the Discord channel. The default
temperature thresholds can be changed in the config.ini file.
"""


import time
import configparser
import logging
import sys
from textwrap import dedent
import mqtt_interface as mqtt
import discord_access as discord

class UI():
    def __init__(self):
        # Read config file to define default threshold parameters and channel nr
        config = configparser.ConfigParser()
        config.read('config.ini')
        config_defaults = config['DEFAULTS']      
        
        self.def_still_val = float(config_defaults['still_full_cd'])
        self.def_still_val_4K_cd = float(config_defaults['still_4K_cd'])
        self.def_still_val_coldinsert = float(config_defaults['still_coldinsert'])
        self.def_baseT_val = float(config_defaults['baseT'])
        self.def_circ_val = float(config_defaults['circ_warning'])
        self.def_warmup_val = float(config_defaults['warmup'])
        
        # define channel numbers of temperature sensors
        self.channel_nr_still = int(config_defaults['channel_nr_still'])
        self.channel_nr_mxc = int(config_defaults['channel_nr_mxc'])
        
        # create objects for mqtt client and discord server
        self.bftc = mqtt.Client_bftc()
        self.discord_server = discord.Discord_access()
        
        # setup logging
        logging.root.handlers = []
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y/%m/%d %H:%M:%S',
                            handlers=[logging.FileHandler("logfile.log"),
                                logging.StreamHandler(sys.stdout)])
        
    # Function definitions for different cooldown and warmup scenarios
    
    def monitor_temp(self,temp_channel, threshold, cooling=True):
        # Subscribes to temp sensors and checks them until the temp of temp_channel
        # is below (or above for cooling=False) the threshold.
        self.bftc.monitor_temp(temp_channel,threshold,cooling)
    
    def still_temp(self,time_start, threshold=5, cooling=True):
        # Monitors still temperature and returns a message with the time it took
        # to reach the threshold.
        self.monitor_temp(self.channel_nr_still,threshold, cooling)
        time_passed = time.time() - time_start
        # check if threshold was reached, otherwise repeat monitoring
        if not self.bftc.threshold_reached:
            self.unexpected_disconnect(time_passed)
            self.still_temp(time_start,threshold,cooling)
        msg = f'Still reached {threshold} K after %.2f h' %(time_passed/3600)
        self.discord_server.send_message(msg)
    
    def mxc_temp(self,time_start, threshold, cooling=True):
        # Monitors mxc temperature and returns a message with the time it took
        # to reach the threshold.
        self.monitor_temp(self.channel_nr_mxc,threshold,cooling)
        time_passed = time.time() - time_start
        # check if threshold was reached, otherwise repeat monitoring
        if not self.bftc.threshold_reached:
            self.unexpected_disconnect(time_passed)
            self.mxc_temp(time_start,threshold,cooling)
        msg = f'MXC reached {threshold*1000} mK after %.2f h' %(time_passed/3600)
        self.discord_server.send_message(msg)
    
    def circulation_mode(self,threshold):
        # Monitors mxc temperature and returns a warning when goes above threshold.
        self.monitor_temp(self.channel_nr_still, threshold, cooling=False)
        # check if threshold was reached, otherwise repeat monitoring
        if not self.bftc.threshold_reached:
            self.unexpected_disconnect()
            self.circulation_mode(threshold)
        msg = f'MXC surpassed {threshold*1000} mK '
        self.discord_server.send_warning(msg)
    
    def full_cooldown(self,still_val,baseT_val,circ_val):
        # Starts full cooldown and reports after still is cold enough for ciculation
        # and after reaching base temperature and then enters circulation mode.
        msg = 'Started full cooldown'
        self.discord_server.send_message(msg)
        self.still_temp(self.start,still_val)
        self.mxc_temp(self.start,baseT_val)
        self.circulation_mode(circ_val)
        
    def cooldown_4K(self,still_val):
        # Starts cooldown to 4K and reports after still is cold enough.
        msg = 'Started cooldown to 4K'
        self.discord_server.send_message(msg)
        self.still_temp(self.start,still_val)    
    
    def condense(self,baseT_val,circ_val):
        # starts condensing and reports after reaching base temperature
        # and then enters circulation mode
        msg = 'Started mixture condensation'
        self.discord_server.send_message(msg)
        self.mxc_temp(self.start,baseT_val)
        self.circulation_mode(circ_val)
    
    def cold_insert(self,still_val,baseT_val,circ_val):
        # Starts cold insert and reports after still is cold enough for ciculation
        # and after reaching base temperature and then enters circulation mode.
        msg = 'Started cold insert'
        self.discord_server.send_message(msg)
        self.still_temp(self.start,still_val)
        self.mxc_temp(self.start,baseT_val)
        self.circulation_mode(circ_val)
    
    def warmup(self,still_val):
        # Starts warm-up and reports after still is warm enough.
        msg = 'Started warmup'
        self.discord_server.send_message(msg)
        self.still_temp(self.start, still_val, cooling=False)
        
    def check_disconnect(self,time=None):
        # Returns a message, that the API was disconnected unexpectedly
        if time:
            msg_time = 'after %.2f h '
        else:
            msg_time = ''
        msg = 'Disconnected from API ' + msg_time + 'before temperature threshold was reached.'
        self.discord_server.send_message(msg)

    # User interface

    def get_cmd_value(self,msg):
        # Converts the ui input to a float if possible, otherwise return None.
        cmd = input(msg)
        if cmd:
            cmd_val = float(cmd)
        else:
            cmd_val = None
        return cmd_val
    
    def program_interface(self):
        # Runs the program interface that asks the user to select the program mode
        # and the desired temperature thresholds. The timer is started once the
        # program has been selected.
        print(dedent('''
              Available commands are:
                  1 -> Full Cooldown
                  2 -> Cooldown to 4K
                  3 -> Warmup
                  4 -> Condensing
                  5 -> Cold Insert
                  6 -> Circulation Mode
                  Nothing -> Exit'''))
        program=input('Please select which program to start: ')
        print('')
        self.start = time.time()
        if not program:
            print('User quited the program')
            return
        elif program=='1':
            print(dedent('''\
                         User selected -> Full Cooldown
                         
                         Please enter temperature thresholds (in K) at which notifications should be sent.
                         1Leave empty to use default values.'''))
            still_val=self.get_cmd_value(f'Still temp before condensing (default is {self.def_still_val}): ')
            baseT_val=self.get_cmd_value(f'Base temp of MXC (default is {self.def_baseT_val}): ')
            circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
            print('')
            if not still_val: still_val=self.def_still_val
            if not baseT_val: baseT_val=self.def_baseT_val
            if not circ_val: circ_val=self.def_circ_val
            self.full_cooldown(still_val,baseT_val,circ_val)
        elif program=='2':
            print(dedent('''\
                         User selected Cooldown to 4K
                         
                         Please enter temperature thresholds (in K) at which notifications should be sent.
                         Leave empty to use default values.'''))
            still_val=self.get_cmd_value(f'Still temp when cold (default is {self.def_still_val_4K_cd}): ')
            print('')
            if not still_val: still_val=self.def_still_val_4K_cd
            self.cooldown_4K(still_val)
        elif program=='3':
            print(dedent('''\
                         User selected Warmup
                         
                         Please enter temperature thresholds (in K) at which notifications should be sent.
                         Leave empty to use default values.'''))
            warmup_val=self.get_cmd_value(f'Still temp when warm (default is {self.def_warmup_val}): ')
            print('')
            if warmup_val: warmup_val=float(warmup_val)
            else: warmup_val=self.def_warmup_val
            self.warmup(warmup_val)
        elif program=='4':
            print(dedent('''\
                         User selected Condensing
                         
                         Please enter temperature thresholds (in K) at which notifications should be sent.
                         Leave empty to use default values.'''))
            baseT_val=self.get_cmd_value(f'Base temp of MXC (default is {self.def_baseT_val}): ')
            circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
            print('')
            if not baseT_val: baseT_val=self.def_baseT_val
            if not circ_val: circ_val=self.def_circ_val
            self.condense(baseT_val,circ_val)
        elif program=='5':
            print(dedent('''\
                         User selected Cold Insert
                         
                         Please enter temperature thresholds (in K) at which notifications should be sent.
                         Leave empty to use default values.'''))
            still_val_coldinsert=self.get_cmd_value('Still temp before condensing (default is {self.def_still_val_coldinsert}): ')
            baseT_val=self.get_cmd_value(f'Base temp of MXC (default is {self.def_baseT_val}): ')
            circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
            print('')
            if not still_val: still_val_coldinsert=self.def_still_val_coldinsert
            if not baseT_val: baseT_val=self.def_baseT_val
            if not circ_val: circ_val=self.def_circ_val
            self.cold_insert(still_val_coldinsert,baseT_val,circ_val)
        elif program=='6':
            print(dedent('''\
                         User selected Circulation Mode
                         
                         Please enter temperature thresholds (in K) at which notifications should be sent.
                         Leave empty to use default values.'''))
            circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
            print('')
            if not circ_val: circ_val=self.def_circ_val
            self.circulation_mode(circ_val)
        else:
            print('Invalid input')
        
        self.program_interface()



# Run the interface
ui = UI()
ui.program_interface()




